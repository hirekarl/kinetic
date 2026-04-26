from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any

import aiosqlite  # type: ignore
from google import genai

from kinetic.models.inputs import CheckInPayload

logger = logging.getLogger(__name__)


class SqliteClient:
    """Handles persistence of check-ins into SQLite (Relational)."""

    def __init__(self, db_path: str = "./kinetic.db", api_key: str | None = None) -> None:
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    async def _init_db(self, db: aiosqlite.Connection) -> None:
        """Create tables if they don't exist."""
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS checkins (
                id TEXT PRIMARY KEY,
                timestamp DATETIME,
                message TEXT,
                embedding TEXT,
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
        await db.commit()

    def get_embedding(self, text: str) -> list[float]:
        """Convert text to vector embedding using Gemini API."""
        if not self.client:
            return [0.0] * 768
        try:
            result = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            return [float(x) for x in result.embeddings[0].values]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return [0.0] * 768

    async def insert_checkin(
        self, payload: CheckInPayload, message: str, liaison_feedback: str | None = None
    ) -> str:
        """Insert a parsed check-in into SQLite."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._init_db(db)
            checkin_id = str(uuid.uuid4())
            ts = datetime.now()
            emb = self.get_embedding(message)

            await db.execute(
                "INSERT INTO checkins (id, timestamp, message, embedding, liaison_feedback) VALUES (?, ?, ?, ?, ?)",
                (checkin_id, ts, message, json.dumps(emb), liaison_feedback),
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

    async def clear_database(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM checkin_tasks")
            await db.execute("DELETE FROM bio_metrics")
            await db.execute("DELETE FROM vibe_checks")
            await db.execute("DELETE FROM tasks")
            await db.execute("DELETE FROM checkins")
            await db.commit()
