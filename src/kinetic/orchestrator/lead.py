from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import asyncpg
import structlog

from kinetic.agents.bio_archivist import BioArchivist, BioArchivistResult
from kinetic.agents.logistics_fixer import LogisticsFixer, LogisticsFixerResult
from kinetic.agents.operational_liaison import LiaisonMetadata, OperationalLiaison
from kinetic.agents.relational_diplomat import RelationalDiplomat, RelationalDiplomatResult
from kinetic.db.base import DatabaseClient
from kinetic.db.postgres_client import PostgresClient
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
from kinetic.orchestrator.triage import (
    aggregate_status,
    assign_stable_ids,
    calculate_roi,
    filter_paused_contacts,
    filter_paused_relational_status,
)
from kinetic.services.pattern_detector import detect_and_update_patterns

log = structlog.get_logger()

# Holds references to fire-and-forget background tasks to prevent GC before completion
_background_tasks: set[asyncio.Task[None]] = set()

# Per-tenant DB client cache keyed by tenant id (SQLite path)
_db_clients: dict[str, DatabaseClient] = {}

# Set by main.py lifespan when DATABASE_URL is present; None means SQLite fallback
_pg_pool: asyncpg.Pool | None = None


def get_db(tenant: str = "default") -> DatabaseClient:
    """Return the appropriate database client for a given tenant.

    When a PostgreSQL pool is available (set by the lifespan handler), always
    returns a PostgresClient bound to the pool and tenant.  Otherwise returns a
    cached SqliteClient, creating and caching one on first access.  The "default"
    tenant resolves its path from SQLITE_DB_PATH; other tenants use
    ``kinetic_{tenant}.db``.

    Args:
        tenant: Tenant identifier string.

    Returns:
        A DatabaseClient instance scoped to the requested tenant.
    """
    if _pg_pool is not None:
        return PostgresClient(_pg_pool, tenant)
    if tenant not in _db_clients:
        if tenant == "default":
            path = os.environ.get("SQLITE_DB_PATH", "./kinetic.db")
        else:
            path = f"./kinetic_{tenant}.db"
        _db_clients[tenant] = SqliteClient(path)
    return _db_clients[tenant]


async def _merge_history(payload: CheckInPayload, db: DatabaseClient) -> CheckInPayload:
    """Hydrate missing payload fields with the latest persisted data from the database.

    For each domain (bio, logistics, relational), if the payload sub-model is absent,
    constructs it from DB history.  If the sub-model is present but individual fields
    are None, fills only those gaps.  Deduplicates tasks by name and vibes by person,
    with the payload's current values taking precedence.

    Args:
        payload: The parsed check-in payload, potentially sparse.
        db: Database client scoped to the current tenant.

    Returns:
        The same payload object, mutated in-place with history merged in.
    """
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

    hist_tasks = await db.get_all_tasks()
    if hist_tasks:
        if payload.logistics is None:
            payload.logistics = LogisticsInput(tasks=[LogisticsTask(**t) for t in hist_tasks])
        else:
            current_names = {t.name for t in payload.logistics.tasks}
            for ht in hist_tasks:
                if ht["name"] not in current_names:
                    payload.logistics.tasks.append(LogisticsTask(**ht))

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


@dataclass
class _AgentRunResult:
    bio_status: BioStatus | None
    logistics_status: LogisticsStatus | None
    relational_status: RelationalStatus | None
    triage_items: list[TriageItem]
    overall: StatusLevel
    roi: ROISummary | None
    behavioral_summary: BehavioralSummary | None
    behavioral_profiles: list[BehavioralProfile] = field(default_factory=list)


async def _run_agents(payload: CheckInPayload, db: DatabaseClient) -> _AgentRunResult:
    """Fire all three domain agents concurrently and aggregate their results.

    Dispatches BioArchivist, LogisticsFixer, and RelationalDiplomat in a single
    asyncio.gather() call.  Agent exceptions are caught and replaced with degraded
    yellow-status fallback results so a single agent failure does not abort the
    response.  After agent execution, fetches behavioral context (summary and
    profiles) and computes the aggregate status and ROI summary.

    Args:
        payload: The fully-hydrated check-in payload.
        db: Database client scoped to the current tenant.

    Returns:
        _AgentRunResult containing all domain statuses, triage items, overall
        status level, ROI summary, and behavioral context.
    """
    rolling_metrics: dict[str, Any] = {"bio": await db.get_recent_bio(limit=7)}

    log.info("agents.dispatch")
    results = await asyncio.gather(
        BioArchivist().process(payload, rolling_metrics),
        LogisticsFixer().process(payload, rolling_metrics),
        RelationalDiplomat().process(payload, rolling_metrics),
        return_exceptions=True,
    )

    bio_result = results[0] if isinstance(results[0], BioArchivistResult) else None
    logistics_result = results[1] if isinstance(results[1], LogisticsFixerResult) else None
    relational_result = results[2] if isinstance(results[2], RelationalDiplomatResult) else None

    if isinstance(results[0], Exception):
        log.error("agent.error", agent="bio_archivist", exc=str(results[0]))
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
        log.error("agent.error", agent="logistics_fixer", exc=str(results[1]))
        logistics_result = LogisticsFixerResult(
            success=False,
            error_message="LogisticsFixer unavailable.",
            status=LogisticsStatus(
                status="yellow",
                error_message=f"Internal error: {results[1]}",
            ),
        )
    if isinstance(results[2], Exception):
        log.error("agent.error", agent="relational_diplomat", exc=str(results[2]))
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
    triage_items = assign_stable_ids(sorted(raw_triage, key=lambda t: t.priority, reverse=True))

    overall = aggregate_status(
        bio_status.status if bio_status else None,
        logistics_status.status if logistics_status else None,
        relational_status.status if relational_status else None,
    )
    roi = calculate_roi(bio_status, logistics_status, relational_status)

    behavioral_summary: BehavioralSummary | None = None
    behavioral_profiles: list[BehavioralProfile] = []
    try:
        behavioral_summary = await db.get_behavioral_summary()
        behavioral_profiles = await db.get_behavioral_profiles()
    except Exception:
        log.exception("Failed to fetch behavioral context — proceeding without it")

    return _AgentRunResult(
        bio_status=bio_status,
        logistics_status=logistics_status,
        relational_status=relational_status,
        triage_items=triage_items,
        overall=overall,
        roi=roi,
        behavioral_summary=behavioral_summary,
        behavioral_profiles=behavioral_profiles,
    )


def _fire_pattern_detection(
    db: DatabaseClient,
    behavioral_summary: BehavioralSummary | None,
    behavioral_profiles: list[BehavioralProfile],
) -> None:
    """Schedule Gemini pattern synthesis as a non-blocking asyncio background task.

    Skips silently when behavioral_summary is None (no data yet to analyse).
    The created task is held in _background_tasks to prevent garbage collection
    before it completes.

    Args:
        db: Database client used by detect_and_update_patterns to persist results.
        behavioral_summary: Summary from get_behavioral_summary(), or None.
        behavioral_profiles: Current list of accumulated profiles.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if behavioral_summary is not None:
        task = asyncio.create_task(
            detect_and_update_patterns(db, behavioral_summary, behavioral_profiles, api_key=api_key)
        )
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)


async def orchestrate(
    payload: CheckInPayload,
    message: str = "",
    history: list[dict[str, str]] | None = None,
    db: DatabaseClient | None = None,
) -> SystemHealthPayload:
    """Blocking orchestration path: run agents, call Liaison, persist, and return.

    Merges history into the payload, dispatches all domain agents, calls the
    OperationalLiaison for a prose response, applies contact pauses and task
    completions, persists the check-in, and fires background pattern detection.

    Args:
        payload: The parsed check-in payload from the LLM parser.
        message: The original user message text (used for persistence).
        history: Prior conversation messages for Liaison context, or None.
        db: Database client to use; defaults to get_db() for the "default" tenant.

    Returns:
        A fully-populated SystemHealthPayload ready to serialise to the client.
    """
    if db is None:
        db = get_db()

    payload = await _merge_history(payload, db)
    run = await _run_agents(payload, db)

    liaison_response = await OperationalLiaison().process(
        message=message,
        overall_status=run.overall,
        triage_items=run.triage_items,
        behavioral_summary=run.behavioral_summary,
        behavioral_profiles=run.behavioral_profiles,
        history=history,
        bio_status=run.bio_status,
        logistics_status=run.logistics_status,
        relational_status=run.relational_status,
    )

    for directive in liaison_response.contact_pauses:
        paused_until = date.today() + timedelta(days=directive.pause_days)
        await db.upsert_contact_pause(directive.person, paused_until.isoformat(), directive.reason)

    active_pauses: list[ContactPause] = []
    try:
        raw_pauses = await db.get_active_pauses()
        active_pauses = [ContactPause(**r) for r in raw_pauses]
    except Exception:
        log.exception("Failed to load active contact pauses — proceeding without filtering")

    for task_name in liaison_response.task_completions:
        try:
            await db.complete_task(task_name)
        except KeyError:
            log.warning("complete_task.not_found", task_name=task_name)

    triage_items = filter_paused_contacts(run.triage_items, active_pauses)
    relational_status = filter_paused_relational_status(run.relational_status, active_pauses)

    if message:
        await db.insert_checkin(payload, message, liaison_response.text)

    _fire_pattern_detection(db, run.behavioral_summary, run.behavioral_profiles)

    return SystemHealthPayload(
        overall_status=run.overall,
        bio=run.bio_status,
        logistics=run.logistics_status,
        relational=relational_status,
        triage_items=triage_items,
        roi_summary=run.roi,
        liaison_feedback=liaison_response.text,
        responding_agent=liaison_response.responding_agent,
        behavioral_profiles=run.behavioral_profiles,
        behavioral_summary=run.behavioral_summary,
        active_pauses=active_pauses,
    )


async def orchestrate_stream(
    payload: CheckInPayload,
    message: str = "",
    history: list[dict[str, str]] | None = None,
    db: DatabaseClient | None = None,
) -> AsyncGenerator[dict[str, str], None]:
    """Async-generator variant of orchestrate(): yields SSE event dicts.

    Event sequence:
      1. {"event": "agents", "data": <SystemHealthPayload JSON, no liaison text>}
      2. {"event": "token",  "data": {"text": "<chunk>"}}  — one per Liaison token
      3. {"event": "done",   "data": <metadata + active_pauses JSON>}
    """
    if db is None:
        db = get_db()

    payload = await _merge_history(payload, db)
    run = await _run_agents(payload, db)

    # Load pre-existing pauses before the first event so the agents card is already filtered
    active_pauses: list[ContactPause] = []
    try:
        raw_pauses = await db.get_active_pauses()
        active_pauses = [ContactPause(**r) for r in raw_pauses]
    except Exception:
        log.exception("Failed to load active pauses in stream")

    filtered_triage = filter_paused_contacts(run.triage_items, active_pauses)
    filtered_relational = filter_paused_relational_status(run.relational_status, active_pauses)

    # ── Event 1: agent cards ───────────────────────────────────────────────────
    agents_payload = SystemHealthPayload(
        overall_status=run.overall,
        bio=run.bio_status,
        logistics=run.logistics_status,
        relational=filtered_relational,
        triage_items=filtered_triage,
        roi_summary=run.roi,
        behavioral_profiles=run.behavioral_profiles,
        behavioral_summary=run.behavioral_summary,
        active_pauses=active_pauses,
    )
    yield {"event": "agents", "data": agents_payload.model_dump_json()}

    # ── Events 2..N: Liaison token stream ─────────────────────────────────────
    liaison = OperationalLiaison()
    accumulated_text = ""
    async for chunk in liaison.stream_text(
        message=message,
        overall_status=run.overall,
        triage_items=filtered_triage,
        behavioral_summary=run.behavioral_summary,
        behavioral_profiles=run.behavioral_profiles,
        history=history,
        bio_status=run.bio_status,
        logistics_status=run.logistics_status,
        relational_status=filtered_relational,
    ):
        accumulated_text += chunk
        yield {"event": "token", "data": json.dumps({"text": chunk})}

    # ── Metadata extraction + side effects ────────────────────────────────────
    metadata: LiaisonMetadata = await liaison.extract_metadata(accumulated_text, message)

    for directive in metadata.contact_pauses:
        paused_until = date.today() + timedelta(days=directive.pause_days)
        await db.upsert_contact_pause(directive.person, paused_until.isoformat(), directive.reason)

    # Reload after upserting — done event must reflect any pauses added this turn
    try:
        raw_pauses = await db.get_active_pauses()
        active_pauses = [ContactPause(**r) for r in raw_pauses]
    except Exception:
        log.exception("Failed to reload active pauses after upsert in stream")

    for task_name in metadata.task_completions:
        try:
            await db.complete_task(task_name)
        except KeyError:
            log.warning("complete_task.not_found", task_name=task_name)

    if message:
        await db.insert_checkin(payload, message, accumulated_text)

    _fire_pattern_detection(db, run.behavioral_summary, run.behavioral_profiles)

    # ── Event final: done ─────────────────────────────────────────────────────
    yield {
        "event": "done",
        "data": json.dumps(
            {
                "responding_agent": metadata.responding_agent,
                "contact_pauses": [p.model_dump() for p in metadata.contact_pauses],
                "task_completions": metadata.task_completions,
                "active_pauses": [p.model_dump() for p in active_pauses],
                "behavioral_profiles": [p.model_dump() for p in run.behavioral_profiles],
                "behavioral_summary": (
                    run.behavioral_summary.model_dump() if run.behavioral_summary else None
                ),
            }
        ),
    }


async def get_current_state(db: DatabaseClient | None = None) -> dict[str, Any]:
    """Retrieve the latest system health snapshot and full conversation history.

    Runs orchestrate() with an empty payload to compute the current dashboard
    state from persisted history, then fetches the last 50 messages.

    Args:
        db: Database client to use; defaults to get_db() for the "default" tenant.

    Returns:
        Dict with keys "health" (SystemHealthPayload) and "messages" (list of
        role/content dicts).
    """
    if db is None:
        db = get_db()

    health = await orchestrate(CheckInPayload(), message="", db=db)
    messages = await db.get_history(limit=50)

    return {"health": health, "messages": messages}
