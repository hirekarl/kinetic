from __future__ import annotations

import json
import logging
import statistics
import uuid
from datetime import date, datetime, timedelta
from itertools import groupby
from typing import Any

import asyncpg

from kinetic.models.inputs import CheckInPayload
from kinetic.models.outputs import (
    BehavioralProfile,
    BehavioralSummary,
    BioTrend,
    RecurringTask,
    RelationalDrift,
)

logger = logging.getLogger(__name__)

_SLEEP_WEIGHT = 0.4
_NUTRITION_WEIGHT = 0.3
_ENERGY_WEIGHT = 0.3
_BASELINE_SLEEP = 8.0
_SLEEP_PENALTY = 25.0


def _compute_burnout_scalar(
    sleep_hours: float | None,
    nutrition_quality: float | None,
    energy_level: float | None,
) -> float:
    """Replicate BioArchivist per-entry burnout formula (no historical debt adjustment)."""
    weighted_sum = 0.0
    total_weight = 0.0
    if sleep_hours is not None:
        deficit = max(0.0, _BASELINE_SLEEP - sleep_hours)
        weighted_sum += _SLEEP_WEIGHT * min(100.0, deficit * _SLEEP_PENALTY)
        total_weight += _SLEEP_WEIGHT
    if nutrition_quality is not None:
        weighted_sum += _NUTRITION_WEIGHT * (10.0 - nutrition_quality) / 9.0 * 100.0
        total_weight += _NUTRITION_WEIGHT
    if energy_level is not None:
        weighted_sum += _ENERGY_WEIGHT * (10.0 - energy_level) / 9.0 * 100.0
        total_weight += _ENERGY_WEIGHT
    if total_weight == 0.0:
        return 0.0
    return round(weighted_sum / total_weight, 2)


_DDL = """
CREATE TABLE IF NOT EXISTS checkins (
    id TEXT PRIMARY KEY,
    tenant TEXT NOT NULL DEFAULT 'default',
    timestamp TIMESTAMPTZ NOT NULL,
    message TEXT,
    liaison_feedback TEXT
);

CREATE TABLE IF NOT EXISTS bio_metrics (
    id TEXT PRIMARY KEY,
    tenant TEXT NOT NULL DEFAULT 'default',
    checkin_id TEXT REFERENCES checkins(id),
    sleep_hours REAL,
    nutrition_quality INTEGER,
    energy_level INTEGER,
    inserted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tasks (
    name TEXT NOT NULL,
    tenant TEXT NOT NULL DEFAULT 'default',
    priority TEXT,
    subtasks TEXT,
    completed_subtasks TEXT,
    status TEXT,
    UNIQUE (name, tenant)
);

CREATE TABLE IF NOT EXISTS checkin_tasks (
    checkin_id TEXT REFERENCES checkins(id),
    task_name TEXT,
    tenant TEXT NOT NULL DEFAULT 'default',
    days_overdue INTEGER,
    inserted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vibe_checks (
    checkin_id TEXT REFERENCES checkins(id),
    person TEXT,
    score INTEGER,
    days_since_contact INTEGER,
    tenant TEXT NOT NULL DEFAULT 'default',
    inserted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS behavioral_profiles (
    tenant TEXT NOT NULL DEFAULT 'default',
    profile_key TEXT NOT NULL,
    insight TEXT NOT NULL,
    evidence TEXT NOT NULL,
    first_observed TIMESTAMPTZ NOT NULL,
    last_updated TIMESTAMPTZ NOT NULL,
    observation_count INTEGER NOT NULL DEFAULT 1,
    UNIQUE (profile_key, tenant)
);

CREATE TABLE IF NOT EXISTS contact_pauses (
    tenant TEXT NOT NULL DEFAULT 'default',
    person TEXT NOT NULL,
    paused_until TEXT NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (person, tenant)
);
"""


class PostgresClient:
    """asyncpg-backed database client with per-tenant row isolation."""

    def __init__(self, pool: asyncpg.Pool, tenant: str) -> None:
        self.pool = pool
        self.tenant = tenant

    async def _migrate(self) -> None:
        """Idempotent DDL — safe to call on every startup."""
        async with self.pool.acquire() as conn:
            await conn.execute(_DDL)

    async def insert_checkin(
        self, payload: CheckInPayload, message: str, liaison_feedback: str | None = None
    ) -> str:
        checkin_id = str(uuid.uuid4())
        ts = datetime.now()
        async with self.pool.acquire() as conn, conn.transaction():
            await conn.execute(
                "INSERT INTO checkins (id, tenant, timestamp, message, liaison_feedback)"
                " VALUES ($1, $2, $3, $4, $5)",
                checkin_id,
                self.tenant,
                ts,
                message,
                liaison_feedback,
            )
            if payload.bio:
                await conn.execute(
                    "INSERT INTO bio_metrics"
                    " (id, tenant, checkin_id, sleep_hours, nutrition_quality, energy_level)"
                    " VALUES ($1, $2, $3, $4, $5, $6)",
                    str(uuid.uuid4()),
                    self.tenant,
                    checkin_id,
                    payload.bio.sleep_hours,
                    payload.bio.nutrition_quality,
                    payload.bio.energy_level,
                )
            if payload.logistics:
                for task in payload.logistics.tasks:
                    await conn.execute(
                        "INSERT INTO tasks"
                        " (tenant, name, priority, subtasks, completed_subtasks, status)"
                        " VALUES ($1, $2, $3, $4, $5, $6)"
                        " ON CONFLICT (name, tenant) DO UPDATE SET"
                        "   priority = EXCLUDED.priority,"
                        "   subtasks = EXCLUDED.subtasks,"
                        "   completed_subtasks = EXCLUDED.completed_subtasks,"
                        "   status = EXCLUDED.status",
                        self.tenant,
                        task.name,
                        task.priority,
                        json.dumps(task.subtasks),
                        json.dumps(task.completed_subtasks),
                        task.status,
                    )
                    await conn.execute(
                        "INSERT INTO checkin_tasks"
                        " (tenant, checkin_id, task_name, days_overdue)"
                        " VALUES ($1, $2, $3, $4)",
                        self.tenant,
                        checkin_id,
                        task.name,
                        task.days_overdue,
                    )
            if payload.relational:
                for vibe in payload.relational.vibe_checks:
                    await conn.execute(
                        "INSERT INTO vibe_checks"
                        " (tenant, checkin_id, person, score, days_since_contact)"
                        " VALUES ($1, $2, $3, $4, $5)",
                        self.tenant,
                        checkin_id,
                        vibe.person,
                        vibe.score,
                        vibe.days_since_contact,
                    )
        return checkin_id

    async def get_latest_bio(self) -> dict[str, Any] | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT sleep_hours, nutrition_quality, energy_level"
                " FROM bio_metrics WHERE tenant = $1"
                " ORDER BY inserted_at DESC LIMIT 1",
                self.tenant,
            )
            return dict(row) if row else None

    async def get_all_tasks(self) -> list[dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT name, priority, subtasks, completed_subtasks, status"
                " FROM tasks WHERE tenant = $1",
                self.tenant,
            )
            results = []
            for r in rows:
                d = dict(r)
                d["subtasks"] = json.loads(d["subtasks"])
                d["completed_subtasks"] = json.loads(d["completed_subtasks"])
                ct = await conn.fetchrow(
                    "SELECT days_overdue FROM checkin_tasks"
                    " WHERE task_name = $1 AND tenant = $2"
                    " ORDER BY inserted_at DESC LIMIT 1",
                    d["name"],
                    self.tenant,
                )
                d["days_overdue"] = ct["days_overdue"] if ct else 0
                results.append(d)
            return results

    async def get_all_vibes(self) -> list[dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT DISTINCT ON (person) person, score, days_since_contact"
                " FROM vibe_checks WHERE tenant = $1"
                " ORDER BY person, inserted_at DESC",
                self.tenant,
            )
            return [dict(r) for r in rows]

    async def get_recent_bio(self, limit: int = 7) -> list[dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT sleep_hours, nutrition_quality, energy_level"
                " FROM bio_metrics WHERE tenant = $1"
                " ORDER BY inserted_at DESC LIMIT $2",
                self.tenant,
                limit,
            )
            return [dict(r) for r in rows]

    async def upsert_contact_pause(
        self, person: str, paused_until: str, reason: str | None
    ) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO contact_pauses (tenant, person, paused_until, reason)"
                " VALUES ($1, $2, $3, $4)"
                " ON CONFLICT (person, tenant) DO UPDATE SET"
                "   paused_until = EXCLUDED.paused_until,"
                "   reason = EXCLUDED.reason",
                self.tenant,
                person,
                paused_until,
                reason,
            )

    async def get_active_pauses(self) -> list[dict[str, Any]]:
        today = date.today().isoformat()
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT person, paused_until, reason FROM contact_pauses"
                " WHERE tenant = $1 AND paused_until >= $2",
                self.tenant,
                today,
            )
            return [dict(r) for r in rows]

    async def get_history(self, limit: int = 20) -> list[dict[str, str]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT message, liaison_feedback, timestamp FROM checkins"
                " WHERE tenant = $1 ORDER BY timestamp ASC LIMIT $2",
                self.tenant,
                limit,
            )
            messages: list[dict[str, str]] = []
            for r in rows:
                messages.append({"role": "user", "content": r["message"] or ""})
                if r["liaison_feedback"]:
                    messages.append({"role": "system", "content": r["liaison_feedback"]})
            return messages

    async def get_behavioral_summary(self, days: int = 14) -> BehavioralSummary:
        cutoff = datetime.now() - timedelta(days=days)
        async with self.pool.acquire() as conn:
            count_row = await conn.fetchrow(
                "SELECT COUNT(DISTINCT timestamp::date) FROM checkins"
                " WHERE tenant = $1 AND timestamp >= $2",
                self.tenant,
                cutoff,
            )
            days_analyzed = int(count_row[0]) if count_row and count_row[0] else 0

            if days_analyzed == 0:
                return BehavioralSummary(days_analyzed=0, generated_at=datetime.now())

            bio_rows = await conn.fetch(
                "SELECT bm.sleep_hours, bm.nutrition_quality, bm.energy_level,"
                " c.timestamp::date AS check_date"
                " FROM bio_metrics bm"
                " JOIN checkins c ON bm.checkin_id = c.id"
                " WHERE c.tenant = $1 AND bm.tenant = $1 AND c.timestamp >= $2"
                " ORDER BY c.timestamp ASC",
                self.tenant,
                cutoff,
            )

            bio_trend: BioTrend | None = None
            if bio_rows:
                sleep_vals = [
                    float(r["sleep_hours"]) for r in bio_rows if r["sleep_hours"] is not None
                ]
                nutrition_vals = [
                    float(r["nutrition_quality"])
                    for r in bio_rows
                    if r["nutrition_quality"] is not None
                ]
                energy_vals = [
                    float(r["energy_level"]) for r in bio_rows if r["energy_level"] is not None
                ]
                dates = [str(r["check_date"]) for r in bio_rows]
                n = len(sleep_vals)
                slope = statistics.linear_regression(range(n), sleep_vals).slope if n >= 2 else 0.0
                worst_day = dates[sleep_vals.index(min(sleep_vals))] if sleep_vals else None
                burnout_vals = [
                    _compute_burnout_scalar(
                        float(r["sleep_hours"]) if r["sleep_hours"] is not None else None,
                        float(r["nutrition_quality"])
                        if r["nutrition_quality"] is not None
                        else None,
                        float(r["energy_level"]) if r["energy_level"] is not None else None,
                    )
                    for r in bio_rows
                ]
                bio_trend = BioTrend(
                    avg_sleep_hours=round(statistics.mean(sleep_vals), 2) if sleep_vals else 0.0,
                    sleep_slope=round(slope, 4),
                    avg_nutrition=round(statistics.mean(nutrition_vals), 2)
                    if nutrition_vals
                    else 0.0,
                    avg_energy=round(statistics.mean(energy_vals), 2) if energy_vals else 0.0,
                    worst_sleep_day=worst_day,
                    days_analyzed=len(set(dates)),
                    sleep_series=sleep_vals,
                    burnout_series=burnout_vals,
                )

            task_rows = await conn.fetch(
                "SELECT ct.task_name, COUNT(*) AS times_overdue,"
                " AVG(ct.days_overdue::float) AS avg_days_overdue, t.priority"
                " FROM checkin_tasks ct"
                " JOIN tasks t ON ct.task_name = t.name AND ct.tenant = t.tenant"
                " JOIN checkins c ON ct.checkin_id = c.id"
                " WHERE ct.tenant = $1 AND ct.days_overdue > 0 AND c.timestamp >= $2"
                " GROUP BY ct.task_name, t.priority"
                " HAVING COUNT(*) > 1"
                " ORDER BY times_overdue DESC",
                self.tenant,
                cutoff,
            )
            recurring = [
                RecurringTask(
                    name=str(r["task_name"]),
                    times_overdue=int(r["times_overdue"]),
                    avg_days_overdue=round(float(r["avg_days_overdue"]), 2),
                    priority=str(r["priority"]),
                )
                for r in task_rows
            ]

            vibe_rows = await conn.fetch(
                "SELECT vc.person, vc.score, vc.days_since_contact"
                " FROM vibe_checks vc"
                " JOIN checkins c ON vc.checkin_id = c.id"
                " WHERE vc.tenant = $1 AND c.timestamp >= $2"
                " ORDER BY vc.person ASC, c.timestamp ASC",
                self.tenant,
                cutoff,
            )
            drifts: list[RelationalDrift] = []
            for person, group in groupby(vibe_rows, key=lambda r: r["person"]):
                entries = list(group)
                if len(entries) < 2:
                    continue
                contact_vals = [int(e["days_since_contact"]) for e in entries]
                score_vals = [float(e["score"]) for e in entries]
                drift_slope = statistics.linear_regression(
                    range(len(contact_vals)), contact_vals
                ).slope
                drifts.append(
                    RelationalDrift(
                        person=str(person),
                        contact_trend=round(drift_slope, 4),
                        avg_vibe_score=round(statistics.mean(score_vals), 2),
                        last_known_days_since_contact=contact_vals[-1],
                    )
                )

            return BehavioralSummary(
                bio_trend=bio_trend,
                recurring_tasks=recurring,
                relational_drifts=drifts,
                days_analyzed=days_analyzed,
                generated_at=datetime.now(),
            )

    async def get_burnout_series(self, days: int = 14) -> list[float]:
        """Return per-entry burnout scores for the last `days` days, oldest→newest."""
        cutoff = datetime.now() - timedelta(days=days)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT bm.sleep_hours, bm.nutrition_quality, bm.energy_level"
                " FROM bio_metrics bm"
                " JOIN checkins c ON bm.checkin_id = c.id"
                " WHERE c.tenant = $1 AND bm.tenant = $1 AND c.timestamp >= $2"
                " ORDER BY c.timestamp ASC",
                self.tenant,
                cutoff,
            )
        return [
            _compute_burnout_scalar(
                float(r["sleep_hours"]) if r["sleep_hours"] is not None else None,
                float(r["nutrition_quality"]) if r["nutrition_quality"] is not None else None,
                float(r["energy_level"]) if r["energy_level"] is not None else None,
            )
            for r in rows
        ]

    async def get_behavioral_profiles(self) -> list[BehavioralProfile]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT profile_key, insight, evidence, first_observed,"
                " last_updated, observation_count"
                " FROM behavioral_profiles WHERE tenant = $1"
                " ORDER BY last_updated DESC",
                self.tenant,
            )
            return [
                BehavioralProfile(
                    profile_key=str(r["profile_key"]),
                    insight=str(r["insight"]),
                    evidence=json.loads(str(r["evidence"])),
                    first_observed=r["first_observed"],
                    last_updated=r["last_updated"],
                    observation_count=int(r["observation_count"]),
                )
                for r in rows
            ]

    async def upsert_behavioral_profile(self, profile: BehavioralProfile) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO behavioral_profiles"
                " (tenant, profile_key, insight, evidence, first_observed, last_updated, observation_count)"
                " VALUES ($1, $2, $3, $4, $5, $6, 1)"
                " ON CONFLICT (profile_key, tenant) DO UPDATE SET"
                "   insight = EXCLUDED.insight,"
                "   evidence = EXCLUDED.evidence,"
                "   last_updated = EXCLUDED.last_updated,"
                "   observation_count = behavioral_profiles.observation_count + 1",
                self.tenant,
                profile.profile_key,
                profile.insight,
                json.dumps(profile.evidence),
                profile.first_observed,
                profile.last_updated,
            )

    async def complete_task(self, task_name: str) -> None:
        async with self.pool.acquire() as conn, conn.transaction():
            row = await conn.fetchrow(
                "SELECT name FROM tasks WHERE name = $1 AND tenant = $2",
                task_name,
                self.tenant,
            )
            if row is None:
                raise KeyError(task_name)
            await conn.execute(
                "UPDATE tasks SET status = 'completed' WHERE name = $1 AND tenant = $2",
                task_name,
                self.tenant,
            )

    async def clear_database(self) -> None:
        async with self.pool.acquire() as conn, conn.transaction():
            await conn.execute("DELETE FROM checkin_tasks WHERE tenant = $1", self.tenant)
            await conn.execute("DELETE FROM vibe_checks WHERE tenant = $1", self.tenant)
            await conn.execute("DELETE FROM bio_metrics WHERE tenant = $1", self.tenant)
            await conn.execute("DELETE FROM checkins WHERE tenant = $1", self.tenant)
            await conn.execute("DELETE FROM tasks WHERE tenant = $1", self.tenant)
            await conn.execute("DELETE FROM contact_pauses WHERE tenant = $1", self.tenant)
            await conn.execute("DELETE FROM behavioral_profiles WHERE tenant = $1", self.tenant)
