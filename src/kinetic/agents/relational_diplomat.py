from __future__ import annotations

from kinetic.agents.base import AgentResult
from kinetic.models.inputs import CheckInPayload, VibeCheck
from kinetic.models.outputs import RelationalStatus, StatusLevel, TriageItem

_STALE_CONTACT_DAYS = 7
_DECAY_RATE = 0.05
_MIN_DECAY = 0.3
_AT_RISK_SCORE_THRESHOLD = 5


def _decay_factor(days_since_contact: int) -> float:
    excess = max(0, days_since_contact - _STALE_CONTACT_DAYS)
    return max(_MIN_DECAY, 1.0 - excess * _DECAY_RATE)


def _adjusted_score(check: VibeCheck) -> float:
    return check.score * _decay_factor(check.days_since_contact)


def _connection_margin(checks: list[VibeCheck]) -> float:
    if not checks:
        return 100.0
    adjusted = [_adjusted_score(c) for c in checks]
    return round(sum(adjusted) / len(adjusted) * 10, 2)


def _is_at_risk(check: VibeCheck) -> bool:
    return check.score < _AT_RISK_SCORE_THRESHOLD or check.days_since_contact > _STALE_CONTACT_DAYS


def _overall_status(checks: list[VibeCheck]) -> StatusLevel:
    if not checks:
        return "green"
    if any(c.score < _AT_RISK_SCORE_THRESHOLD for c in checks):
        return "red"
    if any(c.days_since_contact > _STALE_CONTACT_DAYS for c in checks):
        return "yellow"
    return "green"


def _sprint_suggestion(check: VibeCheck) -> str:
    if check.score < 3:
        return f"Schedule a call with {check.person} this week — connection critical."
    if check.score < _AT_RISK_SCORE_THRESHOLD:
        return f"Text {check.person} to check in — response overdue."
    return f"Drop a quick message to {check.person} — just a check-in."


class RelationalDiplomatResult(AgentResult):
    status: RelationalStatus | None = None


class RelationalDiplomat:
    """Tracks connection margin and recommends interaction sprints."""

    async def process(self, payload: CheckInPayload) -> RelationalDiplomatResult:
        if payload.relational is None:
            return RelationalDiplomatResult(
                success=False, error_message="No relational data in payload."
            )

        checks = payload.relational.vibe_checks
        margin = _connection_margin(checks)
        level = _overall_status(checks)

        at_risk = [c.person for c in checks if _is_at_risk(c)]
        sprints = [_sprint_suggestion(c) for c in checks if _is_at_risk(c)]

        triage: list[TriageItem] = []
        for check in checks:
            if not _is_at_risk(check):
                continue
            priority = 8 if check.score < _AT_RISK_SCORE_THRESHOLD else 5
            triage.append(
                TriageItem(
                    id="relational-temp-0",
                    priority=priority,
                    domain="relational",
                    description=f"{check.person}: vibe {check.score}/10, {check.days_since_contact}d since contact.",
                    action=_sprint_suggestion(check),
                )
            )

        return RelationalDiplomatResult(
            status=RelationalStatus(
                status=level,
                connection_margin_score=margin,
                at_risk_relationships=at_risk,
                interaction_sprints=sprints,
            ),
            triage_items=triage,
        )
