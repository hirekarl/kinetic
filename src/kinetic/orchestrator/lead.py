from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from kinetic.agents.bio_archivist import BioArchivist, BioArchivistResult
from kinetic.agents.logistics_fixer import LogisticsFixer, LogisticsFixerResult
from kinetic.agents.operational_liaison import OperationalLiaison
from kinetic.agents.relational_diplomat import RelationalDiplomat, RelationalDiplomatResult
from kinetic.db.ladybug_client import LadybugClient
from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsInput,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)
from kinetic.models.outputs import (
    BioStatus,
    LogisticsStatus,
    RelationalStatus,
    ROISummary,
    StatusLevel,
    SystemHealthPayload,
    TriageItem,
)

logger = logging.getLogger(__name__)

# Global DB Client
_db_client: LadybugClient | None = None


def get_db() -> LadybugClient:
    global _db_client
    if _db_client is None:
        path = os.environ.get("LADYBUG_DB_PATH", "./.kinetic_db")
        _db_client = LadybugClient(path)
    return _db_client


def _calculate_roi(
    bio: BioStatus | None,
    logistics: LogisticsStatus | None,
    relational: RelationalStatus | None,
) -> ROISummary | None:
    """Calculate ROI based on agent outputs. Returns None if no data."""
    if not any([bio, logistics, relational]):
        return None

    time_saved = 0
    if logistics and logistics.outsourcing_suggestions:
        # If there are outsourcing suggestions, we count the resolve time as 'recovered'
        time_saved = logistics.time_to_resolve_minutes

    # Margin recovered is a qualitative/quantitative mix.
    # We'll use a formula: (time_saved_hours / 16 active hours) + (relational_margin / 100)
    # Re-mapped to a "System Capacity Reclaimed" percentage.
    margin_pct = (time_saved / 960) * 100  # 960 mins = 16h
    if relational:
        # Add 5% for every 10 points of connection margin above 50
        margin_pct += max(0, (relational.connection_margin_score - 50) / 2)

    # Burnout risk delta: Potential improvement if recommendations are followed
    risk_delta = 0.0
    if bio:
        # Each recommendation is estimated to reduce burnout by 8%
        risk_delta = -float(len(bio.recommendations) * 8.0)

    return ROISummary(
        time_recovered_minutes=time_saved,
        margin_recovered=f"{margin_pct:.1f}% capacity reclaimed",
        burnout_risk_delta=risk_delta,
    )


def _aggregate_status(*statuses: StatusLevel | None) -> StatusLevel:
    active = [s for s in statuses if s is not None]
    if not active:
        return "green"
    if "red" in active:
        return "red"
    if "yellow" in active:
        return "yellow"
    return "green"


def _assign_stable_ids(items: list[TriageItem]) -> list[TriageItem]:
    """Re-index triage items with stable domain-scoped IDs after global sort."""
    counters: dict[str, int] = {}
    result: list[TriageItem] = []
    for item in items:
        domain = item.domain
        idx = counters.get(domain, 0)
        counters[domain] = idx + 1
        result.append(item.model_copy(update={"id": f"{domain}-{idx:03d}"}))
    return result


async def _merge_history(payload: CheckInPayload, db: LadybugClient) -> CheckInPayload:
    """Populate missing fields in payload with the latest known data from DB."""
    # 1. Bio
    latest_bio = await db.get_latest_bio()
    if latest_bio:
        if payload.bio is None:
            payload.bio = BioInput(**latest_bio)
        else:
            if payload.bio.sleep_hours is None:
                payload.bio.sleep_hours = latest_bio["sleep_hours"]
            if payload.bio.nutrition_quality is None:
                payload.bio.nutrition_quality = latest_bio["nutrition_quality"]
            if payload.bio.energy_level is None:
                payload.bio.energy_level = latest_bio["energy_level"]

    # 2. Logistics
    hist_tasks = await db.get_all_tasks()
    if hist_tasks:
        if payload.logistics is None:
            payload.logistics = LogisticsInput(tasks=[LogisticsTask(**t) for t in hist_tasks])
        else:
            current_names = {t.name for t in payload.logistics.tasks}
            for ht in hist_tasks:
                if ht["name"] not in current_names:
                    payload.logistics.tasks.append(LogisticsTask(**ht))

    # 3. Relational
    hist_vibes = await db.get_all_vibes()
    if hist_vibes:
        if payload.relational is None:
            payload.relational = RelationalInput(vibe_checks=[VibeCheck(**v) for v in hist_vibes])
        else:
            current_people = {v.person for v in payload.relational.vibe_checks}
            for hv in hist_vibes:
                if hv["person"] not in current_people:
                    payload.relational.vibe_checks.append(VibeCheck(**hv))

    return payload


async def orchestrate(payload: CheckInPayload, message: str = "") -> SystemHealthPayload:
    """Route parsed check-in payload to relevant agents and aggregate results."""
    db = get_db()

    # 1. Persist the current check-in (and get embedding)
    if message:
        await db.insert_checkin(payload, message)

    # 2. Merge history into payload to maintain system context
    payload = await _merge_history(payload, db)

    # 3. Fetch history for context (rolling metrics)
    history: dict[str, Any] = {
        "bio": await db.get_recent_bio(limit=7),
    }

    # 4. Fire agents in parallel
    bio_task = asyncio.create_task(BioArchivist().process(payload, history))
    logistics_task = asyncio.create_task(LogisticsFixer().process(payload, history))
    relational_task = asyncio.create_task(RelationalDiplomat().process(payload, history))

    # Wait for all tasks to complete
    results = await asyncio.gather(
        bio_task,
        logistics_task,
        relational_task,
        return_exceptions=True,
    )

    bio_result = results[0] if isinstance(results[0], BioArchivistResult) else None
    logistics_result = results[1] if isinstance(results[1], LogisticsFixerResult) else None
    relational_result = results[2] if isinstance(results[2], RelationalDiplomatResult) else None

    # Handle exceptions from gather
    if isinstance(results[0], Exception):
        logger.error(f"BioArchivist task failed with exception: {results[0]}")
        bio_result = BioArchivistResult(
            success=False,
            error_message="BioArchivist unavailable.",
            status=BioStatus(
                status="yellow",
                burnout_score=0,
                forecast="Agent failure detected. System monitoring for this sector is degraded.",
                error_message=f"Internal error: {results[0]}",
            ),
        )

    if isinstance(results[1], Exception):
        logger.error(f"LogisticsFixer task failed with exception: {results[1]}")
        logistics_result = LogisticsFixerResult(
            success=False,
            error_message="LogisticsFixer unavailable.",
            status=LogisticsStatus(
                status="yellow",
                error_message=f"Internal error: {results[1]}",
            ),
        )

    if isinstance(results[2], Exception):
        logger.error(f"RelationalDiplomat task failed with exception: {results[2]}")
        relational_result = RelationalDiplomatResult(
            success=False,
            error_message="RelationalDiplomat unavailable.",
            status=RelationalStatus(
                status="yellow",
                connection_margin_score=0,
                error_message=f"Internal error: {results[2]}",
            ),
        )

    bio_status = bio_result.status if bio_result else None
    logistics_status = logistics_result.status if logistics_result else None
    relational_status = relational_result.status if relational_result else None

    raw_triage: list[TriageItem] = []
    for agent_result in (bio_result, logistics_result, relational_result):
        if agent_result is not None:
            raw_triage.extend(agent_result.triage_items)

    sorted_triage = sorted(raw_triage, key=lambda t: t.priority, reverse=True)
    triage_items = _assign_stable_ids(sorted_triage)

    overall = _aggregate_status(
        bio_status.status if bio_status else None,
        logistics_status.status if logistics_status else None,
        relational_status.status if relational_status else None,
    )

    roi = _calculate_roi(bio_status, logistics_status, relational_status)

    # 3. Formulate tactical liaison feedback
    liaison_feedback = await OperationalLiaison().process(
        message=message,
        overall_status=overall,
        triage_items=triage_items,
    )

    return SystemHealthPayload(
        overall_status=overall,
        bio=bio_status,
        logistics=logistics_status,
        relational=relational_status,
        triage_items=triage_items,
        roi_summary=roi,
        liaison_feedback=liaison_feedback,
    )
