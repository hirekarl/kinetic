"""Unit tests for PostgresClient — all 15 interface methods mocked via asyncpg."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from kinetic.db.postgres_client import PostgresClient
from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsInput,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)
from kinetic.models.outputs import BehavioralProfile

# ── Mock helpers ──────────────────────────────────────────────────────────────


def _make_pool() -> tuple[MagicMock, AsyncMock]:
    """Return (pool, conn) with both acquire() and transaction() context managers mocked."""
    pool = MagicMock()
    conn = AsyncMock()

    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)
    pool.acquire.return_value = acquire_cm

    tx_cm = MagicMock()
    tx_cm.__aenter__ = AsyncMock(return_value=None)
    tx_cm.__aexit__ = AsyncMock(return_value=False)
    conn.transaction = MagicMock(return_value=tx_cm)

    return pool, conn


def _client(tenant: str = "test") -> tuple[PostgresClient, AsyncMock]:
    pool, conn = _make_pool()
    return PostgresClient(pool, tenant), conn


def _row(**kwargs: object) -> MagicMock:
    """Build a dict-like row mock supporting both subscript and attribute access."""
    row = MagicMock()
    row.__getitem__ = lambda self, k: kwargs[k]
    row.__iter__ = lambda self: iter(kwargs.items())
    row.keys = lambda: kwargs.keys()
    for k, v in kwargs.items():
        setattr(row, k, v)
    return row


# ── _migrate ─────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_migrate_executes_ddl() -> None:
    """_migrate() calls conn.execute() with the DDL string."""
    client, conn = _client()
    await client._migrate()
    conn.execute.assert_called_once()
    ddl_arg = conn.execute.call_args[0][0]
    assert "CREATE TABLE IF NOT EXISTS checkins" in ddl_arg


# ── insert_checkin ────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_insert_checkin_bio_only_returns_id() -> None:
    """insert_checkin() with bio payload executes INSERT and returns a UUID string."""
    client, _conn = _client()
    payload = CheckInPayload(bio=BioInput(sleep_hours=7.0, nutrition_quality=8, energy_level=7))
    result = await client.insert_checkin(payload, "Slept 7 hours.")
    assert isinstance(result, str)
    assert len(result) == 36  # UUID format


@pytest.mark.unit
@pytest.mark.asyncio
async def test_insert_checkin_empty_payload_still_succeeds() -> None:
    """insert_checkin() with no bio/logistics/relational still inserts a checkin row."""
    client, conn = _client()
    result = await client.insert_checkin(CheckInPayload(), "Just checking in.")
    assert isinstance(result, str)
    # Only the checkin INSERT was called (no sub-table inserts)
    assert conn.execute.call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_insert_checkin_logistics_inserts_task_rows() -> None:
    """insert_checkin() with logistics inserts tasks + checkin_tasks rows."""
    client, conn = _client()
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=2, priority="high")]
        )
    )
    await client.insert_checkin(payload, "laundry overdue")
    # 1 checkin + 1 task upsert + 1 checkin_task insert = 3 executes
    assert conn.execute.call_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_insert_checkin_relational_inserts_vibe_rows() -> None:
    """insert_checkin() with relational payload inserts a vibe_checks row."""
    client, conn = _client()
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=7, days_since_contact=5)]
        )
    )
    await client.insert_checkin(payload, "Marcus check-in")
    # 1 checkin + 1 vibe_checks INSERT = 2 executes
    assert conn.execute.call_count == 2


# ── insert_checkin_at ─────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_insert_checkin_at_returns_id() -> None:
    """insert_checkin_at() inserts with explicit timestamp and returns a UUID."""
    client, _conn = _client()
    ts = datetime.now() - timedelta(days=3)
    result = await client.insert_checkin_at(CheckInPayload(), "historical", ts)
    assert isinstance(result, str)
    assert len(result) == 36


@pytest.mark.unit
@pytest.mark.asyncio
async def test_insert_checkin_at_with_bio() -> None:
    """insert_checkin_at() with bio payload inserts bio_metrics row."""
    client, conn = _client()
    ts = datetime.now() - timedelta(days=2)
    payload = CheckInPayload(bio=BioInput(sleep_hours=7.0, nutrition_quality=8, energy_level=7))
    await client.insert_checkin_at(payload, "sim bio", ts)
    # 1 checkin + 1 bio_metrics = 2 executes
    assert conn.execute.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_insert_checkin_at_with_logistics() -> None:
    """insert_checkin_at() with logistics inserts task rows."""
    client, conn = _client()
    ts = datetime.now() - timedelta(days=2)
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="dishes", days_overdue=1, priority="low")]
        )
    )
    await client.insert_checkin_at(payload, "sim logistics", ts)
    # 1 checkin + 1 task upsert + 1 checkin_task = 3 executes
    assert conn.execute.call_count == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_insert_checkin_at_with_relational() -> None:
    """insert_checkin_at() with relational payload inserts vibe_checks row."""
    client, conn = _client()
    ts = datetime.now() - timedelta(days=2)
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Priya", score=6, days_since_contact=8)]
        )
    )
    await client.insert_checkin_at(payload, "sim relational", ts)
    # 1 checkin + 1 vibe_check = 2 executes
    assert conn.execute.call_count == 2


# ── get_latest_bio ────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_latest_bio_returns_dict_when_row_exists() -> None:
    """get_latest_bio() returns a dict when the DB has a bio row."""
    client, conn = _client()
    conn.fetchrow.return_value = _row(sleep_hours=7.0, nutrition_quality=8, energy_level=7)
    result = await client.get_latest_bio()
    assert result is not None
    assert result["sleep_hours"] == 7.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_latest_bio_returns_none_when_no_rows() -> None:
    """get_latest_bio() returns None when DB has no bio rows."""
    client, conn = _client()
    conn.fetchrow.return_value = None
    result = await client.get_latest_bio()
    assert result is None


# ── get_all_tasks ─────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_tasks_returns_parsed_tasks() -> None:
    """get_all_tasks() parses JSON subtasks fields and merges days_overdue."""
    client, conn = _client()
    task_row = _row(
        name="laundry",
        priority="high",
        subtasks=json.dumps(["sort", "wash"]),
        completed_subtasks=json.dumps([]),
        status="pending",
    )
    conn.fetch.return_value = [task_row]
    conn.fetchrow.return_value = _row(days_overdue=3)
    result = await client.get_all_tasks()
    assert len(result) == 1
    assert result[0]["name"] == "laundry"
    assert result[0]["subtasks"] == ["sort", "wash"]
    assert result[0]["days_overdue"] == 3


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_tasks_returns_empty_when_no_tasks() -> None:
    """get_all_tasks() returns [] when no tasks exist."""
    client, conn = _client()
    conn.fetch.return_value = []
    result = await client.get_all_tasks()
    assert result == []


# ── get_all_vibes ─────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_vibes_returns_vibe_list() -> None:
    """get_all_vibes() returns a list of vibe dicts."""
    client, conn = _client()
    conn.fetch.return_value = [_row(person="Marcus", score=7, days_since_contact=4)]
    result = await client.get_all_vibes()
    assert len(result) == 1
    assert result[0]["person"] == "Marcus"


# ── get_recent_bio ────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_recent_bio_returns_rows() -> None:
    """get_recent_bio() returns bio metric rows."""
    client, conn = _client()
    conn.fetch.return_value = [
        _row(sleep_hours=7.0, nutrition_quality=8, energy_level=7),
        _row(sleep_hours=6.5, nutrition_quality=7, energy_level=6),
    ]
    result = await client.get_recent_bio(limit=5)
    assert len(result) == 2
    assert result[0]["sleep_hours"] == 7.0


# ── upsert_contact_pause ──────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_contact_pause_calls_execute() -> None:
    """upsert_contact_pause() calls conn.execute() with the upsert SQL."""
    client, conn = _client()
    await client.upsert_contact_pause("Marcus", "2026-06-01", "taking a break")
    conn.execute.assert_called_once()
    sql = conn.execute.call_args[0][0]
    assert "ON CONFLICT" in sql


# ── get_active_pauses ─────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_pauses_returns_future_pauses() -> None:
    """get_active_pauses() returns rows for pauses with future paused_until dates."""
    client, conn = _client()
    future = (datetime.now() + timedelta(days=7)).date().isoformat()
    conn.fetch.return_value = [_row(person="Marcus", paused_until=future, reason=None)]
    result = await client.get_active_pauses()
    assert len(result) == 1
    assert result[0]["person"] == "Marcus"


# ── get_history ───────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_history_includes_user_and_system_messages() -> None:
    """get_history() returns user + system (liaison_feedback) message pairs."""
    client, conn = _client()
    conn.fetch.return_value = [
        _row(
            message="Slept 6 hours.", liaison_feedback="Sleep debt noted.", timestamp=datetime.now()
        )
    ]
    result = await client.get_history(limit=20)
    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[1]["role"] == "system"
    assert result[1]["content"] == "Sleep debt noted."


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_history_omits_system_when_no_feedback() -> None:
    """get_history() only emits user message when liaison_feedback is None."""
    client, conn = _client()
    conn.fetch.return_value = [
        _row(message="Just checking in.", liaison_feedback=None, timestamp=datetime.now())
    ]
    result = await client.get_history()
    assert len(result) == 1
    assert result[0]["role"] == "user"


# ── get_behavioral_summary ────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_behavioral_summary_returns_empty_when_no_checkins() -> None:
    """get_behavioral_summary() returns BehavioralSummary with days_analyzed=0 when no data."""
    client, conn = _client()
    count_row = MagicMock()
    count_row.__getitem__ = lambda self, k: 0
    conn.fetchrow.return_value = count_row
    result = await client.get_behavioral_summary()
    assert result.days_analyzed == 0
    assert result.bio_trend is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_behavioral_summary_builds_bio_trend_from_rows() -> None:
    """get_behavioral_summary() builds a BioTrend when bio rows exist."""
    client, conn = _client()
    count_row = MagicMock()
    count_row.__getitem__ = lambda self, k: 3
    conn.fetchrow.return_value = count_row

    bio_rows = [
        _row(sleep_hours=7.0, nutrition_quality=8, energy_level=7, check_date="2026-04-24"),
        _row(sleep_hours=6.5, nutrition_quality=7, energy_level=6, check_date="2026-04-25"),
        _row(sleep_hours=6.0, nutrition_quality=6, energy_level=5, check_date="2026-04-26"),
    ]
    # Return bio_rows for first fetch, [] for tasks and vibes
    conn.fetch.side_effect = [bio_rows, [], []]

    result = await client.get_behavioral_summary()
    assert result.days_analyzed == 3
    assert result.bio_trend is not None
    assert result.bio_trend.avg_sleep_hours == pytest.approx(6.5, rel=0.01)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_behavioral_summary_computes_relational_drift() -> None:
    """get_behavioral_summary() skips persons with 1 vibe entry; builds drift for 2+."""
    client, conn = _client()
    count_row = MagicMock()
    count_row.__getitem__ = lambda self, k: 3
    conn.fetchrow.return_value = count_row

    # "solo" has only 1 entry → skipped; "marcus" has 2 → drift computed
    vibe_rows = [
        _row(person="marcus", score=7, days_since_contact=3),
        _row(person="marcus", score=6, days_since_contact=8),
        _row(person="solo", score=8, days_since_contact=2),
    ]
    conn.fetch.side_effect = [[], [], vibe_rows]

    result = await client.get_behavioral_summary()
    assert any(d.person == "marcus" for d in result.relational_drifts)
    assert all(d.person != "solo" for d in result.relational_drifts)


# ── get_burnout_series ────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_burnout_series_returns_empty_for_zero_days() -> None:
    """get_burnout_series(days=0) returns [] immediately without a DB query."""
    client, conn = _client()
    result = await client.get_burnout_series(days=0)
    assert result == []
    conn.fetch.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_burnout_series_all_none_bio_returns_zero() -> None:
    """_compute_burnout_scalar(None, None, None) → 0.0 when total_weight is 0."""
    client, conn = _client()
    conn.fetch.return_value = [_row(sleep_hours=None, nutrition_quality=None, energy_level=None)]
    result = await client.get_burnout_series(days=7)
    assert result == [0.0]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_burnout_series_computes_scores_from_rows() -> None:
    """get_burnout_series() returns burnout floats from bio_metrics rows."""
    client, conn = _client()
    conn.fetch.return_value = [
        _row(sleep_hours=8.0, nutrition_quality=9, energy_level=9),  # near-perfect
        _row(sleep_hours=4.0, nutrition_quality=3, energy_level=2),  # high burnout
    ]
    result = await client.get_burnout_series(days=7)
    assert len(result) == 2
    assert result[0] < 10.0  # near-perfect → low score
    assert result[1] > 70.0  # high deficit → high score


# ── get_behavioral_profiles ───────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_behavioral_profiles_returns_empty_list() -> None:
    """get_behavioral_profiles() returns [] when no profiles exist."""
    client, conn = _client()
    conn.fetch.return_value = []
    result = await client.get_behavioral_profiles()
    assert result == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_behavioral_profiles_parses_evidence_json() -> None:
    """get_behavioral_profiles() deserializes the evidence JSON field."""
    now = datetime.now()
    client, conn = _client()
    conn.fetch.return_value = [
        _row(
            profile_key="sleep_deficit",
            insight="Consistently undersleeps.",
            evidence=json.dumps({"avg_sleep": 6.2}),
            first_observed=now,
            last_updated=now,
            observation_count=5,
        )
    ]
    result = await client.get_behavioral_profiles()
    assert len(result) == 1
    assert result[0].profile_key == "sleep_deficit"
    assert result[0].evidence == {"avg_sleep": 6.2}


# ── upsert_behavioral_profile ─────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_behavioral_profile_calls_execute() -> None:
    """upsert_behavioral_profile() calls conn.execute() with ON CONFLICT upsert SQL."""
    now = datetime.now()
    client, conn = _client()
    profile = BehavioralProfile(
        profile_key="sleep_deficit",
        insight="Undersleeps before deadlines.",
        evidence={"avg_sleep": 6.1},
        first_observed=now,
        last_updated=now,
        observation_count=3,
    )
    await client.upsert_behavioral_profile(profile)
    conn.execute.assert_called_once()
    sql = conn.execute.call_args[0][0]
    assert "ON CONFLICT" in sql


# ── complete_task ─────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_task_updates_status_when_task_exists() -> None:
    """complete_task() executes UPDATE when task is found."""
    client, conn = _client()
    conn.fetchrow.return_value = _row(name="laundry")
    await client.complete_task("laundry")
    assert conn.execute.call_count == 1
    sql = conn.execute.call_args[0][0]
    assert "status = 'completed'" in sql


@pytest.mark.unit
@pytest.mark.asyncio
async def test_complete_task_raises_keyerror_for_unknown_task() -> None:
    """complete_task() raises KeyError when task is not in the DB."""
    client, conn = _client()
    conn.fetchrow.return_value = None
    with pytest.raises(KeyError):
        await client.complete_task("nonexistent")


# ── clear_database ────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_clear_database_deletes_all_tables() -> None:
    """clear_database() issues DELETE for all 7 tables."""
    client, conn = _client()
    await client.clear_database()
    assert conn.execute.call_count == 7
    deleted_tables = {
        call[0][0].split("FROM")[1].strip().split()[0] for call in conn.execute.call_args_list
    }
    assert "checkin_tasks" in deleted_tables
    assert "checkins" in deleted_tables
    assert "tasks" in deleted_tables
