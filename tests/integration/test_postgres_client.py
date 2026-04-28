"""Integration tests for PostgresClient.

Skipped when DATABASE_URL is not set. Run with:
    DATABASE_URL=postgresql://user:pass@host/db uv run pytest tests/integration/test_postgres_client.py -v
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

import asyncpg
import pytest

from kinetic.db.postgres_client import PostgresClient  # fails until implemented
from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsInput,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)
from kinetic.models.outputs import BehavioralProfile

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set — PostgreSQL integration tests skipped",
)

_TEST_TENANT = "pg_test_tenant"
_OTHER_TENANT = "pg_other_tenant"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def pool() -> asyncpg.Pool:
    p = await asyncpg.create_pool(os.environ["DATABASE_URL"])
    yield p
    await p.close()


@pytest.fixture
async def client(pool: asyncpg.Pool) -> PostgresClient:
    c = PostgresClient(pool, _TEST_TENANT)
    await c._migrate()
    yield c
    await c.clear_database()


@pytest.fixture
def bio_payload() -> CheckInPayload:
    return CheckInPayload(bio=BioInput(sleep_hours=7.0, nutrition_quality=8, energy_level=7))


@pytest.fixture
def full_payload() -> CheckInPayload:
    return CheckInPayload(
        bio=BioInput(sleep_hours=6.0, nutrition_quality=7, energy_level=6),
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=2, priority="high")]
        ),
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=4, days_since_contact=11)]
        ),
    )


# ── insert_checkin ────────────────────────────────────────────────────────────


async def test_insert_checkin_returns_uuid_string(
    client: PostgresClient, full_payload: CheckInPayload
) -> None:
    checkin_id = await client.insert_checkin(full_payload, "status update")
    assert isinstance(checkin_id, str)
    assert len(checkin_id) == 36  # UUID format


async def test_insert_checkin_persists_liaison_feedback(
    client: PostgresClient, full_payload: CheckInPayload
) -> None:
    await client.insert_checkin(full_payload, "msg", liaison_feedback="tactical readout")
    history = await client.get_history()
    system_msgs = [m for m in history if m["role"] == "system"]
    assert any("tactical readout" in m["content"] for m in system_msgs)


async def test_insert_checkin_empty_payload(client: PostgresClient) -> None:
    checkin_id = await client.insert_checkin(CheckInPayload(), "empty check-in")
    assert len(checkin_id) == 36


# ── get_latest_bio ────────────────────────────────────────────────────────────


async def test_get_latest_bio_returns_none_when_empty(client: PostgresClient) -> None:
    assert await client.get_latest_bio() is None


async def test_get_latest_bio_returns_most_recent(
    client: PostgresClient, full_payload: CheckInPayload
) -> None:
    await client.insert_checkin(full_payload, "first")
    newer = CheckInPayload(bio=BioInput(sleep_hours=9.0, nutrition_quality=9, energy_level=9))
    await client.insert_checkin(newer, "second")
    result = await client.get_latest_bio()
    assert result is not None
    assert result["sleep_hours"] == 9.0


# ── get_all_tasks ─────────────────────────────────────────────────────────────


async def test_get_all_tasks_returns_empty_list(client: PostgresClient) -> None:
    assert await client.get_all_tasks() == []


async def test_get_all_tasks_returns_tasks_with_days_overdue(
    client: PostgresClient, full_payload: CheckInPayload
) -> None:
    await client.insert_checkin(full_payload, "msg")
    tasks = await client.get_all_tasks()
    assert len(tasks) == 1
    assert tasks[0]["name"] == "laundry"
    assert tasks[0]["days_overdue"] == 2


async def test_get_all_tasks_upserts_on_conflict(client: PostgresClient) -> None:
    payload1 = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="dishes", days_overdue=1, priority="low")]
        )
    )
    payload2 = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="dishes", days_overdue=3, priority="high")]
        )
    )
    await client.insert_checkin(payload1, "first")
    await client.insert_checkin(payload2, "second")
    tasks = await client.get_all_tasks()
    dishes = [t for t in tasks if t["name"] == "dishes"]
    assert len(dishes) == 1
    assert dishes[0]["priority"] == "high"


# ── get_all_vibes ─────────────────────────────────────────────────────────────


async def test_get_all_vibes_returns_latest_per_person(client: PostgresClient) -> None:
    p1 = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Alice", score=3, days_since_contact=5)]
        )
    )
    p2 = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Alice", score=8, days_since_contact=1)]
        )
    )
    await client.insert_checkin(p1, "first")
    await client.insert_checkin(p2, "second")
    vibes = await client.get_all_vibes()
    alice = [v for v in vibes if v["person"] == "Alice"]
    assert len(alice) == 1
    assert alice[0]["score"] == 8


# ── get_recent_bio ────────────────────────────────────────────────────────────


async def test_get_recent_bio_returns_empty(client: PostgresClient) -> None:
    assert await client.get_recent_bio() == []


async def test_get_recent_bio_respects_limit(client: PostgresClient) -> None:
    for i in range(5):
        p = CheckInPayload(
            bio=BioInput(sleep_hours=float(i + 4), nutrition_quality=7, energy_level=7)
        )
        await client.insert_checkin(p, f"checkin {i}")
    result = await client.get_recent_bio(limit=3)
    assert len(result) == 3


async def test_get_recent_bio_newest_first(client: PostgresClient) -> None:
    old = CheckInPayload(bio=BioInput(sleep_hours=5.0, nutrition_quality=6, energy_level=6))
    new = CheckInPayload(bio=BioInput(sleep_hours=9.0, nutrition_quality=9, energy_level=9))
    await client.insert_checkin(old, "old")
    await client.insert_checkin(new, "new")
    result = await client.get_recent_bio(limit=2)
    assert result[0]["sleep_hours"] == 9.0


# ── contact_pauses ────────────────────────────────────────────────────────────


async def test_get_active_pauses_returns_empty(client: PostgresClient) -> None:
    assert await client.get_active_pauses() == []


async def test_upsert_and_get_active_pauses_future_date(client: PostgresClient) -> None:
    future = (date.today() + timedelta(days=7)).isoformat()
    await client.upsert_contact_pause("Bob", future, "needs space")
    pauses = await client.get_active_pauses()
    assert any(p["person"] == "Bob" for p in pauses)


async def test_get_active_pauses_excludes_past_dates(client: PostgresClient) -> None:
    past = (date.today() - timedelta(days=1)).isoformat()
    await client.upsert_contact_pause("Carol", past, "expired")
    pauses = await client.get_active_pauses()
    assert not any(p["person"] == "Carol" for p in pauses)


async def test_upsert_contact_pause_overwrites_existing(client: PostgresClient) -> None:
    short = (date.today() + timedelta(days=1)).isoformat()
    extended = (date.today() + timedelta(days=30)).isoformat()
    await client.upsert_contact_pause("Dave", short, "short break")
    await client.upsert_contact_pause("Dave", extended, "extended break")
    pauses = await client.get_active_pauses()
    dave = [p for p in pauses if p["person"] == "Dave"]
    assert len(dave) == 1
    assert dave[0]["paused_until"] == extended


# ── get_history ───────────────────────────────────────────────────────────────


async def test_get_history_returns_empty(client: PostgresClient) -> None:
    assert await client.get_history() == []


async def test_get_history_returns_user_and_system_messages(
    client: PostgresClient, full_payload: CheckInPayload
) -> None:
    await client.insert_checkin(full_payload, "user message", liaison_feedback="system reply")
    history = await client.get_history()
    roles = [m["role"] for m in history]
    assert "user" in roles
    assert "system" in roles


async def test_get_history_omits_system_when_no_feedback(
    client: PostgresClient, full_payload: CheckInPayload
) -> None:
    await client.insert_checkin(full_payload, "user message")
    history = await client.get_history()
    assert all(m["role"] == "user" for m in history)


async def test_get_history_respects_limit(
    client: PostgresClient, full_payload: CheckInPayload
) -> None:
    for i in range(10):
        await client.insert_checkin(full_payload, f"msg {i}", liaison_feedback=f"reply {i}")
    history = await client.get_history(limit=3)
    user_msgs = [m for m in history if m["role"] == "user"]
    assert len(user_msgs) == 3


# ── get_behavioral_summary ────────────────────────────────────────────────────


async def test_get_behavioral_summary_empty_returns_zero_days(client: PostgresClient) -> None:
    summary = await client.get_behavioral_summary()
    assert summary.days_analyzed == 0
    assert summary.bio_trend is None
    assert summary.recurring_tasks == []


async def test_get_behavioral_summary_with_bio_data(
    client: PostgresClient, full_payload: CheckInPayload
) -> None:
    await client.insert_checkin(full_payload, "msg")
    summary = await client.get_behavioral_summary()
    assert summary.days_analyzed >= 1


# ── behavioral_profiles ───────────────────────────────────────────────────────


async def test_get_behavioral_profiles_returns_empty(client: PostgresClient) -> None:
    assert await client.get_behavioral_profiles() == []


async def test_upsert_behavioral_profile_inserts_new(client: PostgresClient) -> None:
    profile = BehavioralProfile(
        profile_key="sleep_deficit",
        insight="Consistently sleeping under 7 hours",
        evidence={"avg_hours": 5.8},
        first_observed=datetime.now(),
        last_updated=datetime.now(),
        observation_count=1,
    )
    await client.upsert_behavioral_profile(profile)
    profiles = await client.get_behavioral_profiles()
    assert len(profiles) == 1
    assert profiles[0].profile_key == "sleep_deficit"
    assert profiles[0].evidence == {"avg_hours": 5.8}


async def test_upsert_behavioral_profile_increments_observation_count(
    client: PostgresClient,
) -> None:
    profile = BehavioralProfile(
        profile_key="late_nights",
        insight="Regularly working past midnight",
        evidence={"occurrences": 5},
        first_observed=datetime.now(),
        last_updated=datetime.now(),
        observation_count=1,
    )
    await client.upsert_behavioral_profile(profile)
    await client.upsert_behavioral_profile(profile)
    profiles = await client.get_behavioral_profiles()
    assert profiles[0].observation_count == 2


# ── complete_task ─────────────────────────────────────────────────────────────


async def test_complete_task_marks_status_completed(
    client: PostgresClient, full_payload: CheckInPayload
) -> None:
    await client.insert_checkin(full_payload, "msg")
    await client.complete_task("laundry")
    tasks = await client.get_all_tasks()
    laundry = next(t for t in tasks if t["name"] == "laundry")
    assert laundry["status"] == "completed"


async def test_complete_task_raises_key_error_for_unknown(client: PostgresClient) -> None:
    with pytest.raises(KeyError):
        await client.complete_task("nonexistent_task")


# ── clear_database ────────────────────────────────────────────────────────────


async def test_clear_database_removes_only_own_tenant(
    pool: asyncpg.Pool, bio_payload: CheckInPayload
) -> None:
    c1 = PostgresClient(pool, _TEST_TENANT)
    c2 = PostgresClient(pool, _OTHER_TENANT)
    await c1._migrate()
    await c1.insert_checkin(bio_payload, "tenant a data")
    await c2.insert_checkin(bio_payload, "tenant b data")
    await c1.clear_database()
    assert await c1.get_history() == []
    assert len(await c2.get_history()) >= 1
    await c2.clear_database()


async def test_clear_database_wipes_all_tables(
    client: PostgresClient, full_payload: CheckInPayload
) -> None:
    await client.insert_checkin(full_payload, "msg", liaison_feedback="reply")
    await client.upsert_contact_pause("Eve", (date.today() + timedelta(days=7)).isoformat(), None)
    await client.clear_database()
    assert await client.get_history() == []
    assert await client.get_all_tasks() == []
    assert await client.get_active_pauses() == []
    assert await client.get_latest_bio() is None
