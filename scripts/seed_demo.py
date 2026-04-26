"""Seed kinetic.db with 7 days of demo history for the Pursuit capstone demo."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta

import aiosqlite

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kinetic.db"))

# Seven days of declining sleep (hours) — day[-7] through day[-1]
SLEEP_HOURS = [7.5, 7.0, 6.5, 6.0, 5.5, 5.5, 5.0]

# Laundry overdue days — 0 at day[-7], growing to 6 at day[-1]
LAUNDRY_OVERDUE = [0, 1, 2, 3, 4, 5, 6]

# Marcus vibe scores and days-since-contact — drifting apart over the week
MARCUS_SCORE = [7, 7, 6, 6, 5, 4, 4]
MARCUS_DAYS_SINCE_CONTACT = [3, 4, 5, 6, 7, 8, 9]

CHECKIN_MESSAGES = [
    "Slept well, feeling good. Laundry pile starting.",
    "Decent sleep. Catching up with Marcus felt good earlier this week.",
    "Sleep dropping a bit. Laundry still pending.",
    "Feeling the crunch. Haven't texted Marcus in a few days.",
    "Running on less sleep than I'd like. Laundry is overdue.",
    "Short night. Disconnected from Marcus, laundry mounting.",
    "Sleep compressed again. Feeling the drift.",
]

LIAISON_FEEDBACK = [
    "Systems nominal. Maintain current pace.",
    "Bio trending well. Relational margin solid — keep it up.",
    "Minor sleep dip noted. Address before it compounds.",
    "Sleep degrading. Flag for Marcus — 6 days of drift needs active intervention.",
    "Bio degraded. Logistics and relational pressure building. Prioritize sleep tonight.",
    "Critical accumulation across all three domains. Triage recommended.",
    "Sleep debt and relational drift both critical. Clear highest-priority items before resuming deep work.",
]

BEHAVIORAL_PROFILES = [
    {
        "profile_key": "chronic_sleep_deficit",
        "insight": "Sleep consistently declines ~0.3 hours per weekday — late-night sprints compressing recovery.",
        "evidence": {"avg_weekday_sleep": 6.1, "sleep_slope": -0.32, "days_analyzed": 7},
        "first_observed": (datetime.now() - timedelta(days=7)).isoformat(),
        "last_updated": (datetime.now() - timedelta(days=1)).isoformat(),
        "observation_count": 7,
    },
    {
        "profile_key": "marcus_relational_drift",
        "insight": "Contact with Marcus has been drifting — days since contact doubled over the past week.",
        "evidence": {
            "contact_trend": 1.0,
            "avg_vibe_score": 5.57,
            "last_known_days_since_contact": 9,
        },
        "first_observed": (datetime.now() - timedelta(days=7)).isoformat(),
        "last_updated": (datetime.now() - timedelta(days=1)).isoformat(),
        "observation_count": 7,
    },
]


async def _init_db(db: aiosqlite.Connection) -> None:
    await db.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id TEXT PRIMARY KEY,
            timestamp DATETIME,
            message TEXT,
            liaison_feedback TEXT
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS bio_metrics (
            id TEXT PRIMARY KEY,
            checkin_id TEXT,
            sleep_hours REAL,
            nutrition_quality INTEGER,
            energy_level INTEGER,
            FOREIGN KEY(checkin_id) REFERENCES checkins(id)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            name TEXT PRIMARY KEY,
            priority TEXT,
            subtasks TEXT,
            completed_subtasks TEXT,
            status TEXT
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS checkin_tasks (
            checkin_id TEXT,
            task_name TEXT,
            days_overdue INTEGER,
            FOREIGN KEY(checkin_id) REFERENCES checkins(id),
            FOREIGN KEY(task_name) REFERENCES tasks(name)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS vibe_checks (
            checkin_id TEXT,
            person TEXT,
            score INTEGER,
            days_since_contact INTEGER,
            FOREIGN KEY(checkin_id) REFERENCES checkins(id)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS behavioral_profiles (
            profile_key TEXT PRIMARY KEY,
            insight TEXT NOT NULL,
            evidence TEXT NOT NULL,
            first_observed DATETIME NOT NULL,
            last_updated DATETIME NOT NULL,
            observation_count INTEGER NOT NULL DEFAULT 1
        )
    """)
    import contextlib

    with contextlib.suppress(Exception):
        await db.execute("ALTER TABLE checkins ADD COLUMN liaison_feedback TEXT")
    await db.commit()


async def seed() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await _init_db(db)

        # Clear existing data for a clean demo slate
        await db.execute("DELETE FROM checkin_tasks")
        await db.execute("DELETE FROM bio_metrics")
        await db.execute("DELETE FROM vibe_checks")
        await db.execute("DELETE FROM tasks")
        await db.execute("DELETE FROM checkins")
        await db.execute("DELETE FROM behavioral_profiles")
        await db.commit()
        print("Cleared existing data.")

        # Seed laundry task (will be referenced by every checkin_task row)
        await db.execute(
            "INSERT INTO tasks (name, priority, subtasks, completed_subtasks, status)"
            " VALUES (?, ?, ?, ?, ?)",
            ("laundry", "high", json.dumps([]), json.dumps([]), "pending"),
        )
        await db.commit()

        # Insert 7 days of check-ins
        now = datetime.now()
        checkin_ids: list[str] = []

        for i, offset_days in enumerate(range(7, 0, -1)):
            checkin_id = str(uuid.uuid4())
            checkin_ids.append(checkin_id)
            ts = now - timedelta(days=offset_days, hours=2)  # ~10pm each night

            await db.execute(
                "INSERT INTO checkins (id, timestamp, message, liaison_feedback) VALUES (?, ?, ?, ?)",
                (checkin_id, ts.isoformat(), CHECKIN_MESSAGES[i], LIAISON_FEEDBACK[i]),
            )
            await db.execute(
                "INSERT INTO bio_metrics (id, checkin_id, sleep_hours, nutrition_quality, energy_level)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    checkin_id,
                    SLEEP_HOURS[i],
                    7,  # nutrition roughly okay throughout
                    max(3, 8 - i),  # energy declining with sleep
                ),
            )
            await db.execute(
                "INSERT INTO checkin_tasks (checkin_id, task_name, days_overdue) VALUES (?, ?, ?)",
                (checkin_id, "laundry", LAUNDRY_OVERDUE[i]),
            )
            await db.execute(
                "INSERT INTO vibe_checks (checkin_id, person, score, days_since_contact)"
                " VALUES (?, ?, ?, ?)",
                (checkin_id, "Marcus", MARCUS_SCORE[i], MARCUS_DAYS_SINCE_CONTACT[i]),
            )

        await db.commit()
        print(f"Inserted {len(checkin_ids)} check-ins.")

        # Insert behavioral profiles
        for profile in BEHAVIORAL_PROFILES:
            await db.execute(
                "INSERT INTO behavioral_profiles"
                " (profile_key, insight, evidence, first_observed, last_updated, observation_count)"
                " VALUES (?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(profile_key) DO UPDATE SET"
                "   insight = excluded.insight,"
                "   evidence = excluded.evidence,"
                "   last_updated = excluded.last_updated,"
                "   observation_count = excluded.observation_count",
                (
                    profile["profile_key"],
                    profile["insight"],
                    json.dumps(profile["evidence"]),
                    profile["first_observed"],
                    profile["last_updated"],
                    profile["observation_count"],
                ),
            )

        await db.commit()
        print(f"Inserted {len(BEHAVIORAL_PROFILES)} behavioral profiles.")

    print()
    print("Demo seed complete.")
    print(f"  Database: {DB_PATH}")
    print("  Check-ins: 7 (day-7 through day-1)")
    print(f"  Sleep trend: {SLEEP_HOURS[0]}h → {SLEEP_HOURS[-1]}h (declining)")
    print("  Laundry: 0 → 6 days overdue")
    print(
        f"  Marcus: score {MARCUS_SCORE[0]} → {MARCUS_SCORE[-1]},"
        f" days-since-contact {MARCUS_DAYS_SINCE_CONTACT[0]} → {MARCUS_DAYS_SINCE_CONTACT[-1]}"
    )
    print(f"  Behavioral profiles: {', '.join(str(p['profile_key']) for p in BEHAVIORAL_PROFILES)}")
    print()
    print("Next steps:")
    print("  uv run uvicorn kinetic.main:app --reload --port 8000")
    print("  cd frontend && npm run dev")
    print("  Open http://localhost:5173")


if __name__ == "__main__":
    asyncio.run(seed())
