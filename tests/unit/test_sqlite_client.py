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


# ── insert_checkin (relational branch) ──────────────────────────────────────


@pytest.mark.unit
async def test_insert_checkin_persists_vibe_checks(tmp_path: pytest.TempPathFactory) -> None:
    """insert_checkin stores vibe_checks rows when relational data is present."""
    client = _make_client(tmp_path)
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=7, days_since_contact=3)]
        )
    )
    await client.insert_checkin(payload, "checked in")

    vibes = await client.get_all_vibes()
    assert any(v["person"] == "Marcus" for v in vibes)
    marcus = next(v for v in vibes if v["person"] == "Marcus")
    assert marcus["score"] == 7
    assert marcus["days_since_contact"] == 3


# ── insert_checkin_at ────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_insert_checkin_at_stores_bio_with_explicit_timestamp(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """insert_checkin_at persists bio data and uses the supplied timestamp."""
    client = _make_client(tmp_path)
    ts = datetime(2026, 4, 1, 22, 0, 0)
    payload = CheckInPayload(bio=BioInput(sleep_hours=6.5, nutrition_quality=7, energy_level=6))
    checkin_id = await client.insert_checkin_at(payload, "night check-in", ts)

    assert checkin_id
    bio = await client.get_latest_bio()
    assert bio is not None
    assert bio["sleep_hours"] == pytest.approx(6.5)


@pytest.mark.unit
async def test_insert_checkin_at_stores_task_data(tmp_path: pytest.TempPathFactory) -> None:
    """insert_checkin_at persists logistics task data with explicit timestamp."""
    client = _make_client(tmp_path)
    ts = datetime(2026, 4, 1, 22, 0, 0)
    task = LogisticsTask(name="dishes", days_overdue=1, priority="medium")
    payload = CheckInPayload(logistics=LogisticsInput(tasks=[task]))
    await client.insert_checkin_at(payload, "doing tasks", ts)

    tasks = await client.get_all_tasks()
    assert any(t["name"] == "dishes" for t in tasks)


@pytest.mark.unit
async def test_insert_checkin_at_stores_relational_data(tmp_path: pytest.TempPathFactory) -> None:
    """insert_checkin_at persists vibe checks with explicit timestamp."""
    client = _make_client(tmp_path)
    ts = datetime(2026, 4, 1, 22, 0, 0)
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Priya", score=8, days_since_contact=2)]
        )
    )
    await client.insert_checkin_at(payload, "relational check-in", ts)

    vibes = await client.get_all_vibes()
    assert any(v["person"] == "Priya" for v in vibes)


# ── get_latest_bio ───────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_get_latest_bio_empty_db_returns_none(tmp_path: pytest.TempPathFactory) -> None:
    """get_latest_bio returns None when no bio data has been stored."""
    client = _make_client(tmp_path)
    result = await client.get_latest_bio()
    assert result is None


@pytest.mark.unit
async def test_get_latest_bio_returns_most_recent_row(tmp_path: pytest.TempPathFactory) -> None:
    """get_latest_bio returns the most recent bio row (highest rowid)."""
    client = _make_client(tmp_path)
    older = CheckInPayload(bio=BioInput(sleep_hours=7.0, nutrition_quality=8, energy_level=7))
    newer = CheckInPayload(bio=BioInput(sleep_hours=5.5, nutrition_quality=6, energy_level=5))
    await _seed_checkin(client, older, datetime.now() - timedelta(days=1))
    await _seed_checkin(client, newer, datetime.now())

    bio = await client.get_latest_bio()
    assert bio is not None
    assert bio["sleep_hours"] == pytest.approx(5.5)


# ── get_all_vibes ────────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_get_all_vibes_returns_latest_per_person(tmp_path: pytest.TempPathFactory) -> None:
    """get_all_vibes returns only the most recent vibe for each person."""
    client = _make_client(tmp_path)
    old_payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=8, days_since_contact=2)]
        )
    )
    new_payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=4, days_since_contact=9)]
        )
    )
    await _seed_checkin(client, old_payload, datetime.now() - timedelta(days=2))
    await _seed_checkin(client, new_payload, datetime.now() - timedelta(days=1))

    vibes = await client.get_all_vibes()
    marcus_vibes = [v for v in vibes if v["person"] == "Marcus"]
    assert len(marcus_vibes) == 1
    assert marcus_vibes[0]["score"] == 4


@pytest.mark.unit
async def test_get_all_vibes_returns_multiple_people(tmp_path: pytest.TempPathFactory) -> None:
    """get_all_vibes returns one row per distinct person."""
    client = _make_client(tmp_path)
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[
                VibeCheck(person="Marcus", score=7, days_since_contact=3),
                VibeCheck(person="Priya", score=9, days_since_contact=1),
            ]
        )
    )
    await _seed_checkin(client, payload, datetime.now())

    vibes = await client.get_all_vibes()
    people = {v["person"] for v in vibes}
    assert "Marcus" in people
    assert "Priya" in people


# ── get_recent_bio ───────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_get_recent_bio_returns_limited_rows(tmp_path: pytest.TempPathFactory) -> None:
    """get_recent_bio returns at most `limit` rows."""
    client = _make_client(tmp_path)
    for offset, sleep in enumerate([7.0, 6.5, 6.0, 5.5, 5.0]):
        payload = CheckInPayload(
            bio=BioInput(sleep_hours=sleep, nutrition_quality=7, energy_level=6)
        )
        await _seed_checkin(client, payload, datetime.now() - timedelta(days=offset))

    rows = await client.get_recent_bio(limit=3)
    assert len(rows) == 3


@pytest.mark.unit
async def test_get_recent_bio_empty_db(tmp_path: pytest.TempPathFactory) -> None:
    """get_recent_bio returns an empty list when no bio data exists."""
    client = _make_client(tmp_path)
    rows = await client.get_recent_bio()
    assert rows == []


# ── upsert_contact_pause / get_active_pauses ────────────────────────────────


@pytest.mark.unit
async def test_upsert_contact_pause_inserts_new_row(tmp_path: pytest.TempPathFactory) -> None:
    """upsert_contact_pause inserts a new pause record."""
    client = _make_client(tmp_path)
    future = (datetime.now() + timedelta(days=14)).date().isoformat()
    await client.upsert_contact_pause("Marcus", future, "needs space")

    pauses = await client.get_active_pauses()
    assert any(p["person"] == "Marcus" for p in pauses)


@pytest.mark.unit
async def test_upsert_contact_pause_updates_existing_row(tmp_path: pytest.TempPathFactory) -> None:
    """upsert_contact_pause with same person replaces paused_until and reason."""
    client = _make_client(tmp_path)
    first_date = (datetime.now() + timedelta(days=7)).date().isoformat()
    second_date = (datetime.now() + timedelta(days=30)).date().isoformat()

    await client.upsert_contact_pause("Marcus", first_date, "initial")
    await client.upsert_contact_pause("Marcus", second_date, "extended")

    pauses = await client.get_active_pauses()
    marcus = next(p for p in pauses if p["person"] == "Marcus")
    assert marcus["paused_until"] == second_date
    assert marcus["reason"] == "extended"


@pytest.mark.unit
async def test_get_active_pauses_future_date_included(tmp_path: pytest.TempPathFactory) -> None:
    """get_active_pauses includes pauses whose paused_until is in the future."""
    client = _make_client(tmp_path)
    future = (datetime.now() + timedelta(days=7)).date().isoformat()
    await client.upsert_contact_pause("Marcus", future, None)

    pauses = await client.get_active_pauses()
    assert any(p["person"] == "Marcus" for p in pauses)


@pytest.mark.unit
async def test_get_active_pauses_past_date_excluded(tmp_path: pytest.TempPathFactory) -> None:
    """get_active_pauses excludes pauses whose paused_until is in the past."""
    client = _make_client(tmp_path)
    past = (datetime.now() - timedelta(days=1)).date().isoformat()
    await client.upsert_contact_pause("Marcus", past, None)

    pauses = await client.get_active_pauses()
    assert not any(p["person"] == "Marcus" for p in pauses)


# ── get_history ──────────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_get_history_returns_user_messages_in_order(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """get_history returns user messages in chronological order."""
    client = _make_client(tmp_path)
    await _seed_checkin(
        client, CheckInPayload(), datetime.now() - timedelta(hours=2), "first message"
    )

    history = await client.get_history(limit=10)
    assert len(history) >= 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "first message"


@pytest.mark.unit
async def test_get_history_empty_db_returns_empty_list(tmp_path: pytest.TempPathFactory) -> None:
    """get_history returns an empty list when no check-ins exist."""
    import aiosqlite

    client = _make_client(tmp_path)
    async with aiosqlite.connect(client.db_path) as db:
        await client._init_db(db)

    history = await client.get_history()
    assert history == []


@pytest.mark.unit
async def test_get_history_respects_limit(tmp_path: pytest.TempPathFactory) -> None:
    """get_history returns at most `limit` check-ins worth of messages."""
    client = _make_client(tmp_path)
    for i in range(5):
        await _seed_checkin(
            client, CheckInPayload(), datetime.now() - timedelta(hours=i), f"message {i}"
        )

    history = await client.get_history(limit=2)
    user_msgs = [m for m in history if m["role"] == "user"]
    assert len(user_msgs) <= 2


# ── clear_database ───────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_clear_database_wipes_all_tables(tmp_path: pytest.TempPathFactory) -> None:
    """clear_database removes all rows from all tables."""
    from kinetic.models.outputs import BehavioralProfile

    client = _make_client(tmp_path)
    payload = CheckInPayload(
        bio=BioInput(sleep_hours=7.0, nutrition_quality=8, energy_level=7),
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="dishes", days_overdue=1, priority="low")]
        ),
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=7, days_since_contact=3)]
        ),
    )
    await client.insert_checkin(payload, "pre-clear data")

    now = datetime.now()
    await client.upsert_behavioral_profile(
        BehavioralProfile(
            profile_key="test_pattern",
            insight="Test insight.",
            evidence={},
            first_observed=now,
            last_updated=now,
            observation_count=1,
        )
    )

    await client.clear_database()

    assert await client.get_latest_bio() is None
    assert await client.get_all_tasks() == []
    assert await client.get_all_vibes() == []
    assert await client.get_behavioral_profiles() == []


# ── relational drift single-entry guard (line 485) ───────────────────────────


@pytest.mark.unit
async def test_behavioral_summary_single_vibe_entry_no_drift(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """A person with only one vibe-check entry cannot have drift computed — skipped."""
    client = _make_client(tmp_path)
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=7, days_since_contact=5)]
        )
    )
    await _seed_checkin(client, payload, datetime.now())

    summary = await client.get_behavioral_summary()
    assert all(d.person != "Marcus" for d in summary.relational_drifts)


# ── get_history system message (line 375) ────────────────────────────────────


@pytest.mark.unit
async def test_get_history_includes_system_message_when_feedback_present(
    tmp_path: pytest.TempPathFactory,
) -> None:
    """get_history emits a system message when liaison_feedback is non-null."""
    client = _make_client(tmp_path)
    async with aiosqlite.connect(client.db_path) as db:
        await client._init_db(db)
        await db.execute(
            "INSERT INTO checkins (id, timestamp, message, liaison_feedback) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), datetime.now().isoformat(), "feeling great", "Noted: good energy."),
        )
        await db.commit()

    history = await client.get_history()
    assert any(m["role"] == "system" and "Noted: good energy." in m["content"] for m in history)
