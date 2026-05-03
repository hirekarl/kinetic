"""Seed demo data — SQLite locally or PostgreSQL on Render (detected via DATABASE_URL)."""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta

TENANT = "demo"
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "kinetic_demo.db"))

SLEEP_HOURS = [7.5, 7.0, 6.5, 6.0, 5.5, 5.5, 5.0]
LAUNDRY_OVERDUE = [0, 1, 2, 3, 4, 5, 6]
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


def _print_summary(target: str) -> None:
    print()
    print("Demo seed complete.")
    print(f"  Target:    {target}")
    print(f"  Tenant:    {TENANT}")
    print("  Check-ins: 7 (day-7 through day-1)")
    print(f"  Sleep trend: {SLEEP_HOURS[0]}h → {SLEEP_HOURS[-1]}h (declining)")
    print("  Laundry: 0 → 6 days overdue")
    print(
        f"  Marcus: score {MARCUS_SCORE[0]} → {MARCUS_SCORE[-1]},"
        f" days-since-contact {MARCUS_DAYS_SINCE_CONTACT[0]} → {MARCUS_DAYS_SINCE_CONTACT[-1]}"
    )
    print(f"  Behavioral profiles: {', '.join(str(p['profile_key']) for p in BEHAVIORAL_PROFILES)}")


async def _seed_sqlite() -> None:
    import contextlib

    import aiosqlite

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
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
        with contextlib.suppress(Exception):
            await db.execute("ALTER TABLE checkins ADD COLUMN liaison_feedback TEXT")
        await db.commit()

        await db.execute("DELETE FROM checkin_tasks")
        await db.execute("DELETE FROM bio_metrics")
        await db.execute("DELETE FROM vibe_checks")
        await db.execute("DELETE FROM tasks")
        await db.execute("DELETE FROM checkins")
        await db.execute("DELETE FROM behavioral_profiles")
        await db.commit()
        print("Cleared existing data.")

        await db.execute(
            "INSERT INTO tasks (name, priority, subtasks, completed_subtasks, status)"
            " VALUES (?, ?, ?, ?, ?)",
            ("laundry", "high", json.dumps([]), json.dumps([]), "pending"),
        )
        await db.commit()

        now = datetime.now()
        checkin_ids: list[str] = []

        for i, offset_days in enumerate(range(7, 0, -1)):
            checkin_id = str(uuid.uuid4())
            checkin_ids.append(checkin_id)
            ts = now - timedelta(days=offset_days, hours=2)

            await db.execute(
                "INSERT INTO checkins (id, timestamp, message, liaison_feedback) VALUES (?, ?, ?, ?)",
                (checkin_id, ts.isoformat(), CHECKIN_MESSAGES[i], LIAISON_FEEDBACK[i]),
            )
            await db.execute(
                "INSERT INTO bio_metrics (id, checkin_id, sleep_hours, nutrition_quality, energy_level)"
                " VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), checkin_id, SLEEP_HOURS[i], 7, max(3, 8 - i)),
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

    _print_summary(DB_PATH)
    print()
    print("Next steps:")
    print("  uv run uvicorn kinetic.main:app --reload --port 8000")
    print("  cd frontend && npm run dev")
    print("  Open http://localhost:5173")


async def _seed_postgres(database_url: str) -> None:
    import asyncpg

    conn = await asyncpg.connect(database_url)
    try:
        # Clear demo tenant rows (order matters for FK constraints)
        await conn.execute("DELETE FROM checkin_tasks WHERE tenant = $1", TENANT)
        await conn.execute("DELETE FROM bio_metrics WHERE tenant = $1", TENANT)
        await conn.execute("DELETE FROM vibe_checks WHERE tenant = $1", TENANT)
        await conn.execute("DELETE FROM contact_pauses WHERE tenant = $1", TENANT)
        await conn.execute("DELETE FROM behavioral_profiles WHERE tenant = $1", TENANT)
        await conn.execute("DELETE FROM checkins WHERE tenant = $1", TENANT)
        await conn.execute("DELETE FROM tasks WHERE tenant = $1", TENANT)
        print(f"Cleared existing data for tenant '{TENANT}'.")

        await conn.execute(
            "INSERT INTO tasks (name, tenant, priority, subtasks, completed_subtasks, status)"
            " VALUES ($1, $2, $3, $4, $5, $6)"
            " ON CONFLICT (name, tenant) DO NOTHING",
            "laundry",
            TENANT,
            "high",
            json.dumps([]),
            json.dumps([]),
            "pending",
        )

        now = datetime.now()
        checkin_ids: list[str] = []

        for i, offset_days in enumerate(range(7, 0, -1)):
            checkin_id = str(uuid.uuid4())
            checkin_ids.append(checkin_id)
            ts = now - timedelta(days=offset_days, hours=2)

            await conn.execute(
                "INSERT INTO checkins (id, tenant, timestamp, message, liaison_feedback)"
                " VALUES ($1, $2, $3, $4, $5)",
                checkin_id,
                TENANT,
                ts,
                CHECKIN_MESSAGES[i],
                LIAISON_FEEDBACK[i],
            )
            await conn.execute(
                "INSERT INTO bio_metrics (id, tenant, checkin_id, sleep_hours, nutrition_quality, energy_level)"
                " VALUES ($1, $2, $3, $4, $5, $6)",
                str(uuid.uuid4()),
                TENANT,
                checkin_id,
                SLEEP_HOURS[i],
                7,
                max(3, 8 - i),
            )
            await conn.execute(
                "INSERT INTO checkin_tasks (checkin_id, task_name, tenant, days_overdue)"
                " VALUES ($1, $2, $3, $4)",
                checkin_id,
                "laundry",
                TENANT,
                LAUNDRY_OVERDUE[i],
            )
            await conn.execute(
                "INSERT INTO vibe_checks (checkin_id, person, score, days_since_contact, tenant)"
                " VALUES ($1, $2, $3, $4, $5)",
                checkin_id,
                "Marcus",
                MARCUS_SCORE[i],
                MARCUS_DAYS_SINCE_CONTACT[i],
                TENANT,
            )

        print(f"Inserted {len(checkin_ids)} check-ins.")

        for profile in BEHAVIORAL_PROFILES:
            await conn.execute(
                "INSERT INTO behavioral_profiles"
                " (tenant, profile_key, insight, evidence, first_observed, last_updated, observation_count)"
                " VALUES ($1, $2, $3, $4, $5, $6, $7)"
                " ON CONFLICT (profile_key, tenant) DO UPDATE SET"
                "   insight = EXCLUDED.insight,"
                "   evidence = EXCLUDED.evidence,"
                "   last_updated = EXCLUDED.last_updated,"
                "   observation_count = EXCLUDED.observation_count",
                TENANT,
                profile["profile_key"],
                profile["insight"],
                json.dumps(profile["evidence"]),
                datetime.fromisoformat(str(profile["first_observed"])),
                datetime.fromisoformat(str(profile["last_updated"])),
                profile["observation_count"],
            )

        print(f"Inserted {len(BEHAVIORAL_PROFILES)} behavioral profiles.")
    finally:
        await conn.close()

    host = database_url.split("@")[-1] if "@" in database_url else database_url
    _print_summary(f"postgresql://{host}")
    print()
    print("Next steps:")
    print("  Open https://kinetic-frontend-c2bd.onrender.com")
    print("  Log in as demo / demo, then click Simulate Week to populate the burnout chart.")


async def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        print(f"PostgreSQL mode (DATABASE_URL set) — seeding tenant '{TENANT}'")
        await _seed_postgres(database_url)
    else:
        print(f"SQLite mode — seeding {DB_PATH}")
        await _seed_sqlite()


if __name__ == "__main__":
    asyncio.run(main())
