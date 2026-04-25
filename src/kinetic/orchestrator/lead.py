from __future__ import annotations

import logging

from kinetic.agents.bio_archivist import BioArchivist, BioArchivistResult
from kinetic.agents.logistics_fixer import LogisticsFixer, LogisticsFixerResult
from kinetic.agents.relational_diplomat import RelationalDiplomat, RelationalDiplomatResult
from kinetic.models.inputs import CheckInPayload
from kinetic.models.outputs import StatusLevel, SystemHealthPayload, TriageItem

logger = logging.getLogger(__name__)


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


async def orchestrate(payload: CheckInPayload) -> SystemHealthPayload:
    """Route parsed check-in payload to relevant agents and aggregate results."""
    bio_result: BioArchivistResult | None = None
    logistics_result: LogisticsFixerResult | None = None
    relational_result: RelationalDiplomatResult | None = None

    if payload.bio is not None:
        try:
            bio_result = await BioArchivist().process(payload)
        except Exception:
            logger.exception("BioArchivist failed")
            bio_result = BioArchivistResult(
                success=False, error_message="BioArchivist unavailable."
            )

    if payload.logistics is not None:
        try:
            logistics_result = await LogisticsFixer().process(payload)
        except Exception:
            logger.exception("LogisticsFixer failed")
            logistics_result = LogisticsFixerResult(
                success=False, error_message="LogisticsFixer unavailable."
            )

    if payload.relational is not None:
        try:
            relational_result = await RelationalDiplomat().process(payload)
        except Exception:
            logger.exception("RelationalDiplomat failed")
            relational_result = RelationalDiplomatResult(
                success=False, error_message="RelationalDiplomat unavailable."
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

    return SystemHealthPayload(
        overall_status=overall,
        bio=bio_status,
        logistics=logistics_status,
        relational=relational_status,
        triage_items=triage_items,
    )
