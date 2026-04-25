from __future__ import annotations

from kinetic.agents.bio_archivist import BioArchivist
from kinetic.agents.logistics_fixer import LogisticsFixer
from kinetic.agents.relational_diplomat import RelationalDiplomat
from kinetic.models.inputs import CheckInPayload
from kinetic.models.outputs import StatusLevel, SystemHealthPayload, TriageItem


def _aggregate_status(*statuses: StatusLevel | None) -> StatusLevel:
    active = [s for s in statuses if s is not None]
    if not active:
        return "green"
    if "red" in active:
        return "red"
    if "yellow" in active:
        return "yellow"
    return "green"


async def orchestrate(payload: CheckInPayload) -> SystemHealthPayload:
    """Route parsed check-in payload to relevant agents and aggregate results."""
    bio_status = None
    logistics_status = None
    relational_status = None
    triage_items: list[TriageItem] = []

    if payload.bio is not None:
        bio_result = await BioArchivist().process(payload)
        bio_status = bio_result.status

    if payload.logistics is not None:
        logistics_result = await LogisticsFixer().process(payload)
        logistics_status = logistics_result.status

    if payload.relational is not None:
        relational_result = await RelationalDiplomat().process(payload)
        relational_status = relational_result.status

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
