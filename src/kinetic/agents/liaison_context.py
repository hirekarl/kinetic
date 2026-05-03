from __future__ import annotations

from kinetic.models.outputs import (
    BehavioralProfile,
    BehavioralSummary,
    BioStatus,
    LogisticsStatus,
    RelationalStatus,
)


def format_bio_status(bio: BioStatus) -> str:
    """Return a formatted BIO ARCHIVIST section string for the LLM prompt.

    Args:
        bio: The current BioStatus produced by BioArchivist.

    Returns:
        Multi-line string summarising burnout score, sleep debt, forecast,
        and recommendations.
    """
    lines = ["\n\nBIO ARCHIVIST — Current Status:"]
    lines.append(
        f"Burnout: {bio.burnout_score:.0f}/100 | Sleep Debt: {bio.sleep_debt_hours:.1f}h | Status: {bio.status.upper()}"
    )
    if bio.forecast:
        lines.append(f"Forecast: {bio.forecast}")
    if bio.recommendations:
        lines.append("Recommendations: " + "; ".join(bio.recommendations))
    return "\n".join(lines)


def format_logistics_status(logistics: LogisticsStatus) -> str:
    """Return a formatted LOGISTICS FIXER section string for the LLM prompt.

    Args:
        logistics: The current LogisticsStatus produced by LogisticsFixer.

    Returns:
        Multi-line string listing queue clearance time, critical tasks,
        per-task subtask steps, and outsourcing candidates.
    """
    lines = ["\n\nLOGISTICS FIXER — Current Status:"]
    lines.append(
        f"Status: {logistics.status.upper()} | Queue clearance: {logistics.time_to_resolve_minutes}min"
    )
    if logistics.critical_tasks:
        lines.append("Critical: " + ", ".join(logistics.critical_tasks))
    if logistics.tasks_with_steps:
        for t in logistics.tasks_with_steps:
            steps = ", ".join(t.subtasks) if t.subtasks else "no steps defined"
            lines.append(f"  • {t.name} [{t.priority}]: {steps}")
    if logistics.outsourcing_suggestions:
        lines.append("Outsource candidates: " + "; ".join(logistics.outsourcing_suggestions))
    return "\n".join(lines)


def format_relational_status(relational: RelationalStatus) -> str:
    """Return a formatted RELATIONAL DIPLOMAT section string for the LLM prompt.

    Args:
        relational: The current RelationalStatus produced by RelationalDiplomat.

    Returns:
        Multi-line string showing connection margin score, at-risk relationships,
        and recommended interaction sprints.
    """
    lines = ["\n\nRELATIONAL DIPLOMAT — Current Status:"]
    lines.append(
        f"Status: {relational.status.upper()} | Connection Margin: {relational.connection_margin_score:.0f}/100"
    )
    if relational.at_risk_relationships:
        lines.append("At-risk: " + ", ".join(relational.at_risk_relationships))
    if relational.interaction_sprints:
        lines.append("Sprints: " + "; ".join(relational.interaction_sprints))
    return "\n".join(lines)


def format_behavioral_summary(summary: BehavioralSummary) -> str:
    """Return a formatted BEHAVIORAL CONTEXT section string for the LLM prompt.

    Args:
        summary: The BehavioralSummary aggregated from recent check-in history.

    Returns:
        Multi-line string covering sleep trend, nutrition/energy averages, worst
        sleep day, recurring overdue tasks, and drifting relational contacts.
    """
    lines = ["\n\nBEHAVIORAL CONTEXT (14-day trend):"]
    if summary.bio_trend:
        bt = summary.bio_trend
        lines.append(
            f"Sleep: avg {bt.avg_sleep_hours:.1f} hrs/night, "
            f"trend {bt.sleep_slope:+.2f} hrs/day over {bt.days_analyzed} days"
        )
        lines.append(f"Nutrition: {bt.avg_nutrition:.1f}/10 | Energy: {bt.avg_energy:.1f}/10")
        if bt.worst_sleep_day:
            lines.append(f"Worst sleep: {bt.worst_sleep_day}")
    if summary.recurring_tasks:
        lines.append(
            "Recurring overdue: "
            + ", ".join(f"{t.name} ({t.times_overdue}x)" for t in summary.recurring_tasks)
        )
    if summary.relational_drifts:
        lines.append(
            "Drifting contacts: "
            + ", ".join(
                f"{d.person} (+{d.contact_trend:.1f}d/check-in)" for d in summary.relational_drifts
            )
        )
    return "\n".join(lines)


def format_profiles(profiles: list[BehavioralProfile]) -> str:
    """Return a formatted ESTABLISHED BEHAVIORAL PATTERNS section string for the LLM prompt.

    Args:
        profiles: List of BehavioralProfile objects from pattern detection.

    Returns:
        Multi-line string listing each profile key, insight text, and observation count.
    """
    lines = ["\n\nESTABLISHED BEHAVIORAL PATTERNS:"]
    for p in profiles:
        lines.append(f"- {p.profile_key}: {p.insight} (observed {p.observation_count}x)")
    return "\n".join(lines)
