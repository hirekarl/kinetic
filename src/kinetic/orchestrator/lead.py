from __future__ import annotations

import asyncio
import logging
import os
from datetime import date, timedelta
from typing import Any

from kinetic.agents.bio_archivist import BioArchivist, BioArchivistResult
from kinetic.agents.logistics_fixer import LogisticsFixer, LogisticsFixerResult
from kinetic.agents.operational_liaison import OperationalLiaison
from kinetic.agents.relational_diplomat import RelationalDiplomat, RelationalDiplomatResult
from kinetic.db.sqlite_client import SqliteClient
from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsInput,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)
from kinetic.models.outputs import (
    BehavioralProfile,
    BehavioralSummary,
    BioStatus,
    ContactPause,
    LogisticsStatus,
    RelationalStatus,
    ROISummary,
    StatusLevel,
    SystemHealthPayload,
    TriageItem,
)
from kinetic.services.pattern_detector import detect_and_update_patterns

logger = logging.getLogger(__name__)

# Holds references to fire-and-forget background tasks to prevent GC before completion
_background_tasks: set[asyncio.Task[None]] = set()

# Global DB Client
_db_client: SqliteClient | None = None


def get_db() -> SqliteClient:
    global _db_client
    if _db_client is None:
        path = os.environ.get("SQLITE_DB_PATH", "./kinetic.db")
        _db_client = SqliteClient(path)
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


def _filter_paused_contacts(
    triage_items: list[TriageItem],
    active_pauses: list[ContactPause],
) -> list[TriageItem]:
    if not active_pauses:
        return triage_items
    paused_lower = {p.person.lower() for p in active_pauses}
    return [
        item
        for item in triage_items
        if not (
            item.domain == "relational"
            and any(name in f"{item.description} {item.action}".lower() for name in paused_lower)
        )
    ]


def _filter_paused_relational_status(
    relational: RelationalStatus | None,
    active_pauses: list[ContactPause],
) -> RelationalStatus | None:
    if relational is None or not active_pauses:
        return relational
    paused_lower = {p.person.lower() for p in active_pauses}
    return relational.model_copy(
        update={
            "at_risk_relationships": [
                p for p in relational.at_risk_relationships if p.lower() not in paused_lower
            ],
            "interaction_sprints": [
                s
                for s in relational.interaction_sprints
                if not any(name in s.lower() for name in paused_lower)
            ],
        }
    )


async def _merge_history(payload: CheckInPayload, db: SqliteClient) -> CheckInPayload:
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


async def orchestrate(
    payload: CheckInPayload,
    message: str = "",
    history: list[dict[str, str]] | None = None,
) -> SystemHealthPayload:
    """Route parsed check-in payload to relevant agents and aggregate results."""
    db = get_db()

    # 1. Merge history into payload to maintain system context
    payload = await _merge_history(payload, db)

    # 2. Fetch rolling metrics for agent context
    rolling_metrics: dict[str, Any] = {
        "bio": await db.get_recent_bio(limit=7),
    }

    # 3. Fire agents in parallel
    bio_task = asyncio.create_task(BioArchivist().process(payload, rolling_metrics))
    logistics_task = asyncio.create_task(LogisticsFixer().process(payload, rolling_metrics))
    relational_task = asyncio.create_task(RelationalDiplomat().process(payload, rolling_metrics))

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

    # 4. Fetch behavioral context (non-fatal — defaults to empty on failure)
    behavioral_summary: BehavioralSummary | None = None
    behavioral_profiles: list[BehavioralProfile] = []
    try:
        behavioral_summary = await db.get_behavioral_summary()
        behavioral_profiles = await db.get_behavioral_profiles()
    except Exception:
        logger.exception("Failed to fetch behavioral context — proceeding without it")

    # 5. Formulate tactical liaison feedback (enriched with all agent context)
    liaison_response = await OperationalLiaison().process(
        message=message,
        overall_status=overall,
        triage_items=triage_items,
        behavioral_summary=behavioral_summary,
        behavioral_profiles=behavioral_profiles,
        history=history,
        bio_status=bio_status,
        logistics_status=logistics_status,
        relational_status=relational_status,
    )

    # 6. Persist any contact pauses the liaison extracted, then load all active pauses
    for directive in liaison_response.contact_pauses:
        paused_until = date.today() + timedelta(days=directive.pause_days)
        await db.upsert_contact_pause(directive.person, paused_until.isoformat(), directive.reason)

    active_pauses: list[ContactPause] = []
    try:
        raw_pauses = await db.get_active_pauses()
        active_pauses = [ContactPause(**r) for r in raw_pauses]
    except Exception:
        logger.exception("Failed to load active contact pauses — proceeding without filtering")

    # 7. Apply contact-pause filtering to triage items and relational status
    triage_items = _filter_paused_contacts(triage_items, active_pauses)
    relational_status = _filter_paused_relational_status(relational_status, active_pauses)

    # 8. Persist the current check-in (including feedback)
    if message:
        await db.insert_checkin(payload, message, liaison_response.text)

    # 9. Fire pattern detection as a non-blocking background task
    api_key = os.environ.get("GEMINI_API_KEY")
    if behavioral_summary is not None:
        task = asyncio.create_task(
            detect_and_update_patterns(db, behavioral_summary, behavioral_profiles, api_key=api_key)
        )
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

    return SystemHealthPayload(
        overall_status=overall,
        bio=bio_status,
        logistics=logistics_status,
        relational=relational_status,
        triage_items=triage_items,
        roi_summary=roi,
        liaison_feedback=liaison_response.text,
        responding_agent=liaison_response.responding_agent,
        behavioral_profiles=behavioral_profiles,
        behavioral_summary=behavioral_summary,
        active_pauses=active_pauses,
    )


async def get_current_state() -> dict[str, Any]:
    """Retrieve the current health dashboard and full conversation history."""
    db = get_db()

    # 1. Run orchestration on empty payload to get current health from DB
    health = await orchestrate(CheckInPayload(), message="")

    # 2. Get dialogue history
    messages = await db.get_history(limit=50)

    return {"health": health, "messages": messages}
