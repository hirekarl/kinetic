"""Unit tests for SqliteClient behavioral memory methods."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta

import aiosqlite  # type: ignore
import pytest

from kinetic.db.sqlite_client import SqliteClient
from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsInput,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)
from kinetic.models.outputs import BehavioralProfile, BehavioralSummary


def _make_client(tmp_path: pytest.TempPathFactory) -> SqliteClient:
    return SqliteClient(db_path=str(tmp_path / "test_kinetic.db"))


async def _seed_checkin(
    client: SqliteClient,
    payload: CheckInPayload,
    ts: datetime,
    message: str = "test check-in",
) -> str:
    """Insert a check-in with an explicit timestamp directly via aiosqlite."""
    async with aiosqlite.connect(client.db_path) as db:
        await client._init_db(db)
        checkin_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO checkins (id, timestamp, message, liaison_feedback) VALUES (?, ?, ?, ?)",
            (checkin_id, ts.isoformat(), message, None),
        )
        if payload.bio:
            await db.execute(
                "INSERT INTO bio_metrics"
                " (id, checkin_id, sleep_hours, nutrition_quality, energy_level)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    checkin_id,
                    payload.bio.sleep_hours,
                    payload.bio.nutrition_quality,
                    payload.bio.energy_level,
                ),
            )
        if payload.logistics:
            for task in payload.logistics.tasks:
                await db.execute(
                    "INSERT INTO tasks"
                    " (name, priority, subtasks, completed_subtasks, status)"
                    " VALUES (?, ?, ?, ?, ?)"
                    " ON CONFLICT(name) DO UPDATE SET priority=excluded.priority",
                    (
                        task.name,
                        task.priority,
                        json.dumps(task.subtasks),
                        json.dumps(task.completed_subtasks),
                        task.status,
                    ),
                )
                await db.execute(
                    "INSERT INTO checkin_tasks (checkin_id, task_name, days_overdue)"
                    " VALUES (?, ?, ?)",
                    (checkin_id, task.name, task.days_overdue),
                )
        if payload.relational:
            for vibe in payload.relational.vibe_checks:
                await db.execute(
                    "INSERT INTO vibe_checks"
                    " (checkin_id, person, score, days_since_contact)"
                    " VALUES (?, ?, ?, ?)",
                    (checkin_id, vibe.person, vibe.score, vibe.days_since_contact),
                )
        await db.commit()
    return checkin_id


# ── get_behavioral_summary ───────────────────────────────────────────────────


@pytest.mark.unit
async def test_behavioral_summary_empty_db(tmp_path: pytest.TempPathFactory) -> None:
    client = _make_client(tmp_path)
    summary = await client.get_behavioral_summary()
    assert isinstance(summary, BehavioralSummary)
    assert summary.days_analyzed == 0
    assert summary.bio_trend is None
    assert summary.recurring_tasks == []
    assert summary.relational_drifts == []


@pytest.mark.unit
async def test_behavioral_summary_single_checkin(tmp_path: pytest.TempPathFactory) -> None:
    client = _make_client(tmp_path)
    payload = CheckInPayload(bio=BioInput(sleep_hours=7.0, nutrition_quality=8, energy_level=7))
    await _seed_checkin(client, payload, ts=datetime.now())

    summary = await client.get_behavioral_summary()
    assert summary.days_analyzed == 1
    assert summary.bio_trend is not None
    assert summary.bio_trend.sleep_slope == 0.0  # guard: can't compute slope with 1 point
    assert summary.bio_trend.avg_sleep_hours == pytest.approx(7.0)


@pytest.mark.unit
async def test_behavioral_summary_declining_sleep(tmp_path: pytest.TempPathFactory) -> None:
    client = _make_client(tmp_path)
    # Oldest → newest: 7.0 → 6.5 → 6.0 (declining)
    for offset, sleep in [(2, 7.0), (1, 6.5), (0, 6.0)]:
        payload = CheckInPayload(
            bio=BioInput(sleep_hours=sleep, nutrition_quality=7, energy_level=7)
        )
        await _seed_checkin(client, payload, ts=datetime.now() - timedelta(days=offset))

    summary = await client.get_behavioral_summary()
    assert summary.bio_trend is not None
    assert summary.bio_trend.sleep_slope < 0


@pytest.mark.unit
async def test_behavioral_summary_improving_sleep(tmp_path: pytest.TempPathFactory) -> None:
    client = _make_client(tmp_path)
    # Oldest → newest: 6.0 → 6.5 → 7.0 (improving)
    for offset, sleep in [(2, 6.0), (1, 6.5), (0, 7.0)]:
        payload = CheckInPayload(
            bio=BioInput(sleep_hours=sleep, nutrition_quality=7, energy_level=7)
        )
        await _seed_checkin(client, payload, ts=datetime.now() - timedelta(days=offset))

    summary = await client.get_behavioral_summary()
    assert summary.bio_trend is not None
    assert summary.bio_trend.sleep_slope > 0


@pytest.mark.unit
async def test_behavioral_summary_recurring_task_detected(
    tmp_path: pytest.TempPathFactory,
) -> None:
    client = _make_client(tmp_path)
    task = LogisticsTask(name="laundry", days_overdue=3, priority="high")
    payload = CheckInPayload(logistics=LogisticsInput(tasks=[task]))

    await _seed_checkin(client, payload, ts=datetime.now() - timedelta(days=2))
    await _seed_checkin(client, payload, ts=datetime.now() - timedelta(days=1))

    summary = await client.get_behavioral_summary()
    names = [t.name for t in summary.recurring_tasks]
    assert "laundry" in names
    laundry = next(t for t in summary.recurring_tasks if t.name == "laundry")
    assert laundry.times_overdue == 2


@pytest.mark.unit
async def test_behavioral_summary_single_overdue_not_recurring(
    tmp_path: pytest.TempPathFactory,
) -> None:
    client = _make_client(tmp_path)
    task = LogisticsTask(name="groceries", days_overdue=2, priority="medium")
    payload = CheckInPayload(logistics=LogisticsInput(tasks=[task]))

    await _seed_checkin(client, payload, ts=datetime.now() - timedelta(days=1))

    summary = await client.get_behavioral_summary()
    names = [t.name for t in summary.recurring_tasks]
    assert "groceries" not in names


@pytest.mark.unit
async def test_behavioral_summary_relational_drift_detected(
    tmp_path: pytest.TempPathFactory,
) -> None:
    client = _make_client(tmp_path)
    # Marcus: days_since_contact increasing across 3 check-ins → positive drift
    for offset, days_contact in [(2, 5), (1, 8), (0, 12)]:
        payload = CheckInPayload(
            relational=RelationalInput(
                vibe_checks=[VibeCheck(person="Marcus", score=7, days_since_contact=days_contact)]
            )
        )
        await _seed_checkin(client, payload, ts=datetime.now() - timedelta(days=offset))

    summary = await client.get_behavioral_summary()
    drifters = [d.person for d in summary.relational_drifts]
    assert "Marcus" in drifters
    marcus = next(d for d in summary.relational_drifts if d.person == "Marcus")
    assert marcus.contact_trend > 0


# ── sleep_series in BioTrend ─────────────────────────────────────────────────


@pytest.mark.unit
async def test_bio_trend_sleep_series_populated(tmp_path: pytest.TempPathFactory) -> None:
    client = _make_client(tmp_path)
    # Insert 3 days oldest→newest: 7.5, 7.0, 6.5
    for offset, sleep in [(2, 7.5), (1, 7.0), (0, 6.5)]:
        payload = CheckInPayload(
            bio=BioInput(sleep_hours=sleep, nutrition_quality=7, energy_level=7)
        )
        await _seed_checkin(client, payload, ts=datetime.now() - timedelta(days=offset))

    summary = await client.get_behavioral_summary()
    assert summary.bio_trend is not None
    assert summary.bio_trend.sleep_series == [7.5, 7.0, 6.5]


@pytest.mark.unit
async def test_bio_trend_sleep_series_empty_when_no_bio(tmp_path: pytest.TempPathFactory) -> None:
    client = _make_client(tmp_path)
    summary = await client.get_behavioral_summary()
    # Empty DB → bio_trend is None; sleep_series is not accessible but the model default is []
    assert summary.bio_trend is None


# ── get_behavioral_profiles + upsert_behavioral_profile ─────────────────────


@pytest.mark.unit
async def test_get_behavioral_profiles_empty(tmp_path: pytest.TempPathFactory) -> None:
    client = _make_client(tmp_path)
    profiles = await client.get_behavioral_profiles()
    assert profiles == []


@pytest.mark.unit
async def test_upsert_and_get_behavioral_profile(tmp_path: pytest.TempPathFactory) -> None:
    client = _make_client(tmp_path)
    now = datetime.now().replace(microsecond=0)
    profile = BehavioralProfile(
        profile_key="sleep_deficit_pattern",
        insight="Consistently sleeps under 7 hours Sunday through Tuesday.",
        evidence={"avg_sleep": 6.2, "days": ["Sun", "Mon", "Tue"]},
        first_observed=now,
        last_updated=now,
        observation_count=1,
    )
    await client.upsert_behavioral_profile(profile)

    profiles = await client.get_behavioral_profiles()
    assert len(profiles) == 1
    assert profiles[0].profile_key == "sleep_deficit_pattern"
    assert "7 hours" in profiles[0].insight
    assert profiles[0].observation_count == 1


@pytest.mark.unit
async def test_upsert_behavioral_profile_increments_count(
    tmp_path: pytest.TempPathFactory,
) -> None:
    client = _make_client(tmp_path)
    first_time = datetime(2026, 4, 25, 10, 0, 0)
    second_time = datetime(2026, 4, 26, 10, 0, 0)

    await client.upsert_behavioral_profile(
        BehavioralProfile(
            profile_key="work_boundary_violation",
            insight="Frequently works past 10pm.",
            evidence={"late_sessions": 3},
            first_observed=first_time,
            last_updated=first_time,
            observation_count=1,
        )
    )
    await client.upsert_behavioral_profile(
        BehavioralProfile(
            profile_key="work_boundary_violation",
            insight="Works past 10pm on average 4 nights per week.",
            evidence={"late_sessions": 5},
            first_observed=second_time,  # must be ignored on conflict
            last_updated=second_time,
            observation_count=1,  # implementation increments; expect final = 2
        )
    )

    profiles = await client.get_behavioral_profiles()
    assert len(profiles) == 1
    p = profiles[0]
    assert p.observation_count == 2
    assert "4 nights" in p.insight  # updated insight
    assert p.first_observed.replace(microsecond=0) == first_time  # must NOT change
    assert p.last_updated.replace(microsecond=0) == second_time  # must update


# ── Task completion ───────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_task_marks_existing_task_completed(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """complete_task() sets status='completed' for an existing task row."""
    client = _make_client(tmp_path)
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=2, priority="high")]
        )
    )
    await _seed_checkin(client, payload, datetime.now())

    await client.complete_task("laundry")

    tasks = await client.get_all_tasks()
    laundry = next((t for t in tasks if t["name"] == "laundry"), None)
    assert laundry is not None
    assert laundry["status"] == "completed"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_task_raises_key_error_for_unknown_task(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """complete_task() raises KeyError when the task name is not in the DB."""
    client = _make_client(tmp_path)
    async with aiosqlite.connect(client.db_path) as db:
        await client._init_db(db)

    with pytest.raises(KeyError, match="nonexistent_task"):
        await client.complete_task("nonexistent_task")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_task_idempotent_for_already_completed(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """complete_task() on an already-completed task does not raise and status stays completed."""
    client = _make_client(tmp_path)
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=2, priority="high")]
        )
    )
    await _seed_checkin(client, payload, datetime.now())

    await client.complete_task("laundry")
    await client.complete_task("laundry")  # second call must not raise

    tasks = await client.get_all_tasks()
    laundry = next((t for t in tasks if t["name"] == "laundry"), None)
    assert laundry is not None
    assert laundry["status"] == "completed"
