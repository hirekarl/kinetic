from __future__ import annotations

from kinetic.models.outputs import (
    BioStatus,
    ContactPause,
    LogisticsStatus,
    RelationalStatus,
    ROISummary,
    StatusLevel,
    TriageItem,
)


def calculate_roi(
    bio: BioStatus | None,
    logistics: LogisticsStatus | None,
    relational: RelationalStatus | None,
) -> ROISummary | None:
    """Compute an ROI summary from agent statuses.

    Estimates time recovered from outsourcing logistics tasks, adds relational
    margin above baseline (50/100 connection score), and calculates burnout risk
    delta from the number of bio recommendations generated.  Returns None when
    all three inputs are absent.

    Args:
        bio: BioStatus from BioArchivist, or None.
        logistics: LogisticsStatus from LogisticsFixer, or None.
        relational: RelationalStatus from RelationalDiplomat, or None.

    Returns:
        ROISummary with time_recovered_minutes, margin_recovered, and
        burnout_risk_delta, or None if no agent data is available.
    """
    if not any([bio, logistics, relational]):
        return None

    time_saved = 0
    if logistics and logistics.outsourcing_suggestions:
        time_saved = logistics.time_to_resolve_minutes

    margin_pct = (time_saved / 960) * 100  # 960 mins = 16h
    if relational:
        margin_pct += max(0, (relational.connection_margin_score - 50) / 2)

    risk_delta = 0.0
    if bio:
        risk_delta = -float(len(bio.recommendations) * 8.0)

    return ROISummary(
        time_recovered_minutes=time_saved,
        margin_recovered=f"{margin_pct:.1f}% capacity reclaimed",
        burnout_risk_delta=risk_delta,
    )


def aggregate_status(*statuses: StatusLevel | None) -> StatusLevel:
    """Return the worst-case status level across all provided domain statuses.

    Ignores None inputs.  Precedence: red > yellow > green.  Returns "green"
    when all inputs are None.

    Args:
        *statuses: Any number of StatusLevel | None values.

    Returns:
        The highest-severity StatusLevel present, or "green" if none are set.
    """
    active = [s for s in statuses if s is not None]
    if not active:
        return "green"
    if "red" in active:
        return "red"
    if "yellow" in active:
        return "yellow"
    return "green"


def assign_stable_ids(items: list[TriageItem]) -> list[TriageItem]:
    """Re-index triage items with stable domain-scoped IDs after global sort."""
    counters: dict[str, int] = {}
    result: list[TriageItem] = []
    for item in items:
        domain = item.domain
        idx = counters.get(domain, 0)
        counters[domain] = idx + 1
        result.append(item.model_copy(update={"id": f"{domain}-{idx:03d}"}))
    return result


def filter_paused_contacts(
    triage_items: list[TriageItem],
    active_pauses: list[ContactPause],
) -> list[TriageItem]:
    """Remove relational triage items that mention a currently-paused contact.

    Matching is case-insensitive and checks both the item's description and
    action fields.  Non-relational items are always kept.

    Args:
        triage_items: The full list of triage items to filter.
        active_pauses: Active contact pauses from the database.

    Returns:
        Filtered list with paused-contact relational items removed.
    """
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


def filter_paused_relational_status(
    relational: RelationalStatus | None,
    active_pauses: list[ContactPause],
) -> RelationalStatus | None:
    """Remove paused contacts from at_risk_relationships and interaction_sprints.

    Returns the original object unchanged when relational is None or there are
    no active pauses.  Matching is case-insensitive.

    Args:
        relational: The RelationalStatus to filter, or None.
        active_pauses: Active contact pauses from the database.

    Returns:
        A new RelationalStatus with paused contacts removed, or the original
        value if no filtering was needed.
    """
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
