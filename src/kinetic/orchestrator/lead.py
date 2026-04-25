from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from kinetic.agents.bio_archivist import BioArchivist, BioArchivistResult
from kinetic.agents.logistics_fixer import LogisticsFixer, LogisticsFixerResult
from kinetic.agents.relational_diplomat import RelationalDiplomat, RelationalDiplomatResult
from kinetic.db.ladybug_client import LadybugClient
from kinetic.models.inputs import CheckInPayload
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


async def orchestrate(payload: CheckInPayload, message: str = "") -> SystemHealthPayload:
    """Route parsed check-in payload to relevant agents and aggregate results."""
    db = get_db()

    # 1. Persist the current check-in (and get embedding)
    if message:
        await db.insert_checkin(payload, message)

    # 2. Fetch history for context
    history: dict[str, Any] = {
        "bio": db.get_recent_bio(limit=7),
        # Add logistics/relational history if needed
    }

    bio_task = None
    logistics_task = None
    relational_task = None

    if payload.bio is not None:
        bio_task = asyncio.create_task(BioArchivist().process(payload, history))

    if payload.logistics is not None:
        logistics_task = asyncio.create_task(LogisticsFixer().process(payload, history))

    if payload.relational is not None:
        relational_task = asyncio.create_task(RelationalDiplomat().process(payload, history))

    # Wait for all tasks to complete
    results = await asyncio.gather(
        bio_task if bio_task else asyncio.sleep(0, result=None),
        logistics_task if logistics_task else asyncio.sleep(0, result=None),
        relational_task if relational_task else asyncio.sleep(0, result=None),
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

    return SystemHealthPayload(
        overall_status=overall,
        bio=bio_status,
        logistics=logistics_status,
        relational=relational_status,
        triage_items=triage_items,
        roi_summary=roi,
    )
