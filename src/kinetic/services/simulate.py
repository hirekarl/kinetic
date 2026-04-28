"""Simulate Week service — inserts 5 pre-scripted check-ins with historical timestamps.

Used exclusively by the demo tenant to populate trend charts and the weekly digest
with a plausible week of data before a live presentation.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from kinetic.db.base import DatabaseClient
from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsInput,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)

# Five scripted snapshots: baseline → mild decline → stress peak → recovery onset.
# Timestamps are spread evenly across the past 7 days at insertion time.
_SIMULATE_SCRIPTS: list[tuple[str, CheckInPayload]] = [
    (
        "Good night's sleep, ate well, high energy. Quarterly report is on track.",
        CheckInPayload(
            bio=BioInput(sleep_hours=7.8, nutrition_quality=8, energy_level=8),
            logistics=LogisticsInput(
                tasks=[LogisticsTask(name="Quarterly report", priority="high", days_overdue=0)]
            ),
            relational=RelationalInput(
                vibe_checks=[VibeCheck(person="Marcus", score=8, days_since_contact=2)]
            ),
        ),
    ),
    (
        "Slept a bit less, still feeling okay. Report slipped two days.",
        CheckInPayload(
            bio=BioInput(sleep_hours=6.5, nutrition_quality=7, energy_level=6),
            logistics=LogisticsInput(
                tasks=[LogisticsTask(name="Quarterly report", priority="high", days_overdue=2)]
            ),
            relational=RelationalInput(
                vibe_checks=[VibeCheck(person="Marcus", score=7, days_since_contact=4)]
            ),
        ),
    ),
    (
        "Sleep is slipping. Laundry piling up. Feeling disconnected from Marcus.",
        CheckInPayload(
            bio=BioInput(sleep_hours=5.8, nutrition_quality=5, energy_level=5),
            logistics=LogisticsInput(
                tasks=[
                    LogisticsTask(name="Laundry", priority="medium", days_overdue=3),
                    LogisticsTask(name="Quarterly report", priority="high", days_overdue=4),
                ]
            ),
            relational=RelationalInput(
                vibe_checks=[VibeCheck(person="Marcus", score=5, days_since_contact=6)]
            ),
        ),
    ),
    (
        "Only 5 hours sleep. Eating badly. Laundry critical. Haven't talked to Marcus in over a week.",
        CheckInPayload(
            bio=BioInput(sleep_hours=5.0, nutrition_quality=4, energy_level=4),
            logistics=LogisticsInput(
                tasks=[LogisticsTask(name="Laundry", priority="medium", days_overdue=5)]
            ),
            relational=RelationalInput(
                vibe_checks=[VibeCheck(person="Marcus", score=4, days_since_contact=8)]
            ),
        ),
    ),
    (
        "Got 6.8 hours last night — starting to recover. Laundry still overdue.",
        CheckInPayload(
            bio=BioInput(sleep_hours=6.8, nutrition_quality=7, energy_level=6),
            logistics=LogisticsInput(
                tasks=[LogisticsTask(name="Laundry", priority="medium", days_overdue=6)]
            ),
            relational=RelationalInput(
                vibe_checks=[VibeCheck(person="Marcus", score=4, days_since_contact=9)]
            ),
        ),
    ),
]


async def simulate_week(db: DatabaseClient) -> int:
    """Insert the 5 scripted check-ins spread across the past 7 days.

    Returns the number of check-ins inserted (always 5 unless the script list changes).
    Timestamps run from (now - 7 days) to (now - 1 day), evenly spaced.
    """
    n = len(_SIMULATE_SCRIPTS)
    now = datetime.now()
    start = now - timedelta(days=7)
    end = now - timedelta(days=1)
    span = end - start

    for i, (message, payload) in enumerate(_SIMULATE_SCRIPTS):
        fraction = i / max(n - 1, 1)
        ts = start + timedelta(seconds=span.total_seconds() * fraction)
        await db.insert_checkin_at(payload, message, ts)

    return n
