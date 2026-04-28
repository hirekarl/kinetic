from __future__ import annotations

import contextlib
import json
import logging
import os
import statistics
import uuid
from datetime import datetime
from itertools import groupby
from typing import Any

import aiosqlite

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


class SqliteClient:
    """Handles persistence of check-ins into SQLite (Relational)."""

    def __init__(self, db_path: str = "./kinetic.db") -> None:
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    async def _init_db(self, db: aiosqlite.Connection) -> None:
        """Create tables if they don't exist."""
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS checkins (
                id TEXT PRIMARY KEY,
                timestamp DATETIME,
                message TEXT,
                liaison_feedback TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS bio_metrics (
                id TEXT PRIMARY KEY,
                checkin_id TEXT,
                sleep_hours REAL,
                nutrition_quality INTEGER,
                energy_level INTEGER,
                FOREIGN KEY(checkin_id) REFERENCES checkins(id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                name TEXT PRIMARY KEY,
                priority TEXT,
                subtasks TEXT,
                completed_subtasks TEXT,
                status TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS checkin_tasks (
                checkin_id TEXT,
                task_name TEXT,
                days_overdue INTEGER,
                FOREIGN KEY(checkin_id) REFERENCES checkins(id),
                FOREIGN KEY(task_name) REFERENCES tasks(name)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS vibe_checks (
                checkin_id TEXT,
                person TEXT,
                score INTEGER,
                days_since_contact INTEGER,
                FOREIGN KEY(checkin_id) REFERENCES checkins(id)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS behavioral_profiles (
                profile_key TEXT PRIMARY KEY,
                insight TEXT NOT NULL,
                evidence TEXT NOT NULL,
                first_observed DATETIME NOT NULL,
                last_updated DATETIME NOT NULL,
                observation_count INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_pauses (
                person TEXT PRIMARY KEY,
                paused_until TEXT NOT NULL,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Column migration: swallow error when column already exists
        # (SQLite has no ALTER TABLE ... ADD COLUMN IF NOT EXISTS)
        with contextlib.suppress(Exception):
            await db.execute("ALTER TABLE checkins ADD COLUMN liaison_feedback TEXT")
        await db.commit()

    async def insert_checkin(
        self, payload: CheckInPayload, message: str, liaison_feedback: str | None = None
    ) -> str:
        """Insert a parsed check-in into SQLite."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            checkin_id = str(uuid.uuid4())
            ts = datetime.now()

            await db.execute(
                "INSERT INTO checkins (id, timestamp, message, liaison_feedback) VALUES (?, ?, ?, ?)",
                (checkin_id, ts, message, liaison_feedback),
            )

            if payload.bio:
                await db.execute(
                    "INSERT INTO bio_metrics (id, checkin_id, sleep_hours, nutrition_quality, energy_level) VALUES (?, ?, ?, ?, ?)",
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
                        """
                        INSERT INTO tasks (name, priority, subtasks, completed_subtasks, status)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(name) DO UPDATE SET
                            priority=excluded.priority,
                            subtasks=excluded.subtasks,
                            completed_subtasks=excluded.completed_subtasks,
                            status=excluded.status
                        """,
                        (
                            task.name,
                            task.priority,
                            json.dumps(task.subtasks),
                            json.dumps(task.completed_subtasks),
                            task.status,
                        ),
                    )
                    await db.execute(
                        "INSERT INTO checkin_tasks (checkin_id, task_name, days_overdue) VALUES (?, ?, ?)",
                        (checkin_id, task.name, task.days_overdue),
                    )

            if payload.relational:
                for vibe in payload.relational.vibe_checks:
                    await db.execute(
                        "INSERT INTO vibe_checks (checkin_id, person, score, days_since_contact) VALUES (?, ?, ?, ?)",
                        (checkin_id, vibe.person, vibe.score, vibe.days_since_contact),
                    )

            await db.commit()
            return checkin_id

    async def get_latest_bio(self) -> dict[str, Any] | None:
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT sleep_hours, nutrition_quality, energy_level FROM bio_metrics ORDER BY rowid DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_all_tasks(self) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM tasks") as cursor:
                rows = await cursor.fetchall()
                results = []
                for r in rows:
                    d = dict(r)
                    d["subtasks"] = json.loads(d["subtasks"])
                    d["completed_subtasks"] = json.loads(d["completed_subtasks"])
                    # Mock days_overdue for now or fetch from last checkin_tasks
                    async with db.execute(
                        "SELECT days_overdue FROM checkin_tasks WHERE task_name = ? ORDER BY rowid DESC LIMIT 1",
                        (d["name"],),
                    ) as cur2:
                        task_log = await cur2.fetchone()
                        d["days_overdue"] = task_log[0] if task_log else 0
                    results.append(d)
                return results

    async def get_all_vibes(self) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            db.row_factory = aiosqlite.Row
            # Get latest vibe for each person
            async with db.execute(
                """
                SELECT person, score, days_since_contact
                FROM vibe_checks
                WHERE rowid IN (SELECT MAX(rowid) FROM vibe_checks GROUP BY person)
                """
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_recent_bio(self, limit: int = 7) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT sleep_hours, nutrition_quality, energy_level FROM bio_metrics ORDER BY rowid DESC LIMIT ?",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def upsert_contact_pause(
        self, person: str, paused_until: str, reason: str | None
    ) -> None:
        """Insert or replace a contact pause (keyed by person name)."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            await db.execute(
                """
                INSERT INTO contact_pauses (person, paused_until, reason)
                VALUES (?, ?, ?)
                ON CONFLICT(person) DO UPDATE SET paused_until=excluded.paused_until, reason=excluded.reason
                """,
                (person, paused_until, reason),
            )
            await db.commit()

    async def get_active_pauses(self) -> list[dict[str, Any]]:
        """Return contact pauses that have not yet expired."""
        from datetime import date

        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT person, paused_until, reason FROM contact_pauses WHERE paused_until >= ?",
                (today,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_history(self, limit: int = 20) -> list[dict[str, str]]:
        """Fetch check-in and liaison history for dialogue hydration."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT message, liaison_feedback, timestamp FROM checkins ORDER BY timestamp ASC LIMIT ?",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
                messages = []
                for r in rows:
                    messages.append({"role": "user", "content": r["message"]})
                    if r["liaison_feedback"]:
                        messages.append({"role": "system", "content": r["liaison_feedback"]})
                return messages

    async def get_behavioral_summary(self, days: int = 14) -> BehavioralSummary:
        """Compute a structured behavioral summary from the last `days` days of check-ins."""
        offset = f"-{days} days"
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)

            # Total distinct check-in days in window
            async with db.execute(
                "SELECT COUNT(DISTINCT DATE(timestamp)) FROM checkins"
                " WHERE timestamp >= datetime('now', ?)",
                (offset,),
            ) as cur:
                row = await cur.fetchone()
                days_analyzed: int = int(row[0]) if row and row[0] else 0

            if days_analyzed == 0:
                return BehavioralSummary(
                    days_analyzed=0,
                    generated_at=datetime.now(),
                )

            # Bio trend
            bio_trend: BioTrend | None = None
            async with db.execute(
                "SELECT bm.sleep_hours, bm.nutrition_quality, bm.energy_level,"
                " DATE(c.timestamp) as check_date"
                " FROM bio_metrics bm"
                " JOIN checkins c ON bm.checkin_id = c.id"
                " WHERE c.timestamp >= datetime('now', ?)"
                " ORDER BY c.timestamp ASC",
                (offset,),
            ) as cur:
                bio_rows = await cur.fetchall()

            if bio_rows:
                sleep_vals = [float(r[0]) for r in bio_rows if r[0] is not None]
                nutrition_vals = [float(r[1]) for r in bio_rows if r[1] is not None]
                energy_vals = [float(r[2]) for r in bio_rows if r[2] is not None]
                dates = [str(r[3]) for r in bio_rows]

                n = len(sleep_vals)
                slope = statistics.linear_regression(range(n), sleep_vals).slope if n >= 2 else 0.0
                worst_day = dates[sleep_vals.index(min(sleep_vals))] if sleep_vals else None
                burnout_vals = [
                    _compute_burnout_scalar(
                        float(r[0]) if r[0] is not None else None,
                        float(r[1]) if r[1] is not None else None,
                        float(r[2]) if r[2] is not None else None,
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

            # Recurring overdue tasks (appeared overdue in ≥2 check-ins)
            recurring: list[RecurringTask] = []
            async with db.execute(
                "SELECT ct.task_name, COUNT(*) as times_overdue,"
                " AVG(CAST(ct.days_overdue AS REAL)) as avg_days_overdue,"
                " t.priority"
                " FROM checkin_tasks ct"
                " JOIN tasks t ON ct.task_name = t.name"
                " JOIN checkins c ON ct.checkin_id = c.id"
                " WHERE ct.days_overdue > 0"
                " AND c.timestamp >= datetime('now', ?)"
                " GROUP BY ct.task_name"
                " HAVING COUNT(*) > 1"
                " ORDER BY times_overdue DESC",
                (offset,),
            ) as cur:
                task_rows = await cur.fetchall()

            for r in task_rows:
                recurring.append(
                    RecurringTask(
                        name=str(r[0]),
                        times_overdue=int(r[1]),
                        avg_days_overdue=round(float(r[2]), 2),
                        priority=str(r[3]),
                    )
                )

            # Relational drift (people whose days_since_contact is trending upward)
            drifts: list[RelationalDrift] = []
            async with db.execute(
                "SELECT vc.person, vc.score, vc.days_since_contact"
                " FROM vibe_checks vc"
                " JOIN checkins c ON vc.checkin_id = c.id"
                " WHERE c.timestamp >= datetime('now', ?)"
                " ORDER BY vc.person ASC, c.timestamp ASC",
                (offset,),
            ) as cur:
                vibe_rows = await cur.fetchall()

            for person, group in groupby(vibe_rows, key=lambda r: r[0]):
                entries = list(group)
                if len(entries) < 2:
                    continue
                contact_vals = [int(e[2]) for e in entries]
                score_vals = [float(e[1]) for e in entries]
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
        offset = f"-{days} days"
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            async with db.execute(
                "SELECT bm.sleep_hours, bm.nutrition_quality, bm.energy_level"
                " FROM bio_metrics bm"
                " JOIN checkins c ON bm.checkin_id = c.id"
                " WHERE c.timestamp >= datetime('now', ?)"
                " ORDER BY c.timestamp ASC",
                (offset,),
            ) as cursor:
                rows = await cursor.fetchall()
        return [
            _compute_burnout_scalar(
                float(r[0]) if r[0] is not None else None,
                float(r[1]) if r[1] is not None else None,
                float(r[2]) if r[2] is not None else None,
            )
            for r in rows
        ]

    async def get_behavioral_profiles(self) -> list[BehavioralProfile]:
        """Return all accumulated behavioral profiles, newest-updated first."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            async with db.execute(
                "SELECT profile_key, insight, evidence, first_observed,"
                " last_updated, observation_count"
                " FROM behavioral_profiles ORDER BY last_updated DESC"
            ) as cur:
                rows = await cur.fetchall()

            return [
                BehavioralProfile(
                    profile_key=str(r[0]),
                    insight=str(r[1]),
                    evidence=json.loads(str(r[2])),
                    first_observed=datetime.fromisoformat(str(r[3])),
                    last_updated=datetime.fromisoformat(str(r[4])),
                    observation_count=int(r[5]),
                )
                for r in rows
            ]

    async def upsert_behavioral_profile(self, profile: BehavioralProfile) -> None:
        """Insert or update a behavioral profile. first_observed is never overwritten."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            await db.execute(
                "INSERT INTO behavioral_profiles"
                " (profile_key, insight, evidence, first_observed, last_updated, observation_count)"
                " VALUES (?, ?, ?, ?, ?, 1)"
                " ON CONFLICT(profile_key) DO UPDATE SET"
                "   insight = excluded.insight,"
                "   evidence = excluded.evidence,"
                "   last_updated = excluded.last_updated,"
                "   observation_count = observation_count + 1",
                (
                    profile.profile_key,
                    profile.insight,
                    json.dumps(profile.evidence),
                    profile.first_observed.isoformat(),
                    profile.last_updated.isoformat(),
                ),
            )
            await db.commit()

    async def complete_task(self, task_name: str) -> None:
        """Mark a task as completed. Raises KeyError if the task does not exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            async with db.execute("SELECT name FROM tasks WHERE name = ?", (task_name,)) as cur:
                row = await cur.fetchone()
            if row is None:
                raise KeyError(task_name)
            await db.execute("UPDATE tasks SET status = 'completed' WHERE name = ?", (task_name,))
            await db.commit()

    async def clear_database(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM checkin_tasks")
            await db.execute("DELETE FROM bio_metrics")
            await db.execute("DELETE FROM vibe_checks")
            await db.execute("DELETE FROM tasks")
            await db.execute("DELETE FROM checkins")
            await db.execute("DELETE FROM behavioral_profiles")
            await db.commit()
