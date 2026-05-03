from __future__ import annotations

from typing import Any

from kinetic.agents.base import AgentResult
from kinetic.models.inputs import BioInput, CheckInPayload
from kinetic.models.outputs import BioStatus, StatusLevel, TriageItem

_SLEEP_WEIGHT = 0.4
_NUTRITION_WEIGHT = 0.3
_ENERGY_WEIGHT = 0.3
_BASELINE_SLEEP_HOURS = 8.0
_SLEEP_PENALTY_PER_HOUR = 25.0  # 4h deficit → score 100


def _sleep_component(sleep_hours: float) -> float:
    """Return a 0-100 burnout contribution from sleep deficit."""
    deficit = max(0.0, _BASELINE_SLEEP_HOURS - sleep_hours)
    return min(100.0, deficit * _SLEEP_PENALTY_PER_HOUR)


def _nutrition_component(quality: int) -> float:
    """Return a 0-100 burnout contribution from nutrition quality (1-10 scale)."""
    return (10 - quality) / 9.0 * 100.0


def _energy_component(level: int) -> float:
    """Return a 0-100 burnout contribution from energy level (1-10 scale)."""
    return (10 - level) / 9.0 * 100.0


def _burnout_status(score: float) -> StatusLevel:
    """Map a 0-100 burnout score to a green/yellow/red status level."""
    if score < 40:
        return "green"
    if score < 70:
        return "yellow"
    return "red"


def _compute_burnout(
    bio: BioInput, history: list[dict[str, Any]] | None = None
) -> tuple[float, float]:
    """Return (burnout_score 0-100, sleep_debt_hours)."""
    weighted_sum = 0.0
    total_weight = 0.0

    if bio.sleep_hours is not None:
        weighted_sum += _SLEEP_WEIGHT * _sleep_component(bio.sleep_hours)
        total_weight += _SLEEP_WEIGHT

    if bio.nutrition_quality is not None:
        weighted_sum += _NUTRITION_WEIGHT * _nutrition_component(bio.nutrition_quality)
        total_weight += _NUTRITION_WEIGHT

    if bio.energy_level is not None:
        weighted_sum += _ENERGY_WEIGHT * _energy_component(bio.energy_level)
        total_weight += _ENERGY_WEIGHT

    if total_weight == 0.0:
        return 0.0, 0.0

    score = round(weighted_sum / total_weight, 2)

    if history:
        recent_sleep = [h.get("sleep_hours", _BASELINE_SLEEP_HOURS) for h in history]
        if bio.sleep_hours is not None:
            recent_sleep.append(bio.sleep_hours)

        total_deficit = sum(max(0.0, _BASELINE_SLEEP_HOURS - s) for s in recent_sleep)
        debt = round(total_deficit, 2)
        if debt > 10:
            score = min(100.0, score + (debt - 10) * 2)
    else:
        debt = round(
            max(0.0, _BASELINE_SLEEP_HOURS - (bio.sleep_hours or _BASELINE_SLEEP_HOURS)), 2
        )

    return score, debt


def _forecast(level: StatusLevel, score: float) -> str:
    """Return a one-sentence burnout forecast message for the given status level and score."""
    if level == "green":
        return f"Low burnout risk (score {score:.0f}). Recovery margin healthy."
    if level == "yellow":
        return f"Moderate burnout risk (score {score:.0f}). Hard stop by 11pm recommended."
    return f"High burnout risk (score {score:.0f}). Recovery actions needed today."


def _recommendations(level: StatusLevel, bio: BioInput) -> list[str]:
    """Build a prioritized list of recovery recommendations based on status and bio inputs.

    Returns an empty list when the status is green and no sleep deficit is present.

    Args:
        level: Current burnout status level.
        bio: The bio input fields from the current check-in.

    Returns:
        Ordered list of actionable recommendation strings.
    """
    recs: list[str] = []
    if bio.sleep_hours is not None and bio.sleep_hours < 7.0:
        debt = round(_BASELINE_SLEEP_HOURS - bio.sleep_hours, 1)
        recs.append(f"Target {_BASELINE_SLEEP_HOURS:.0f}h sleep tonight to recover {debt}h debt.")
    if (
        level in ("yellow", "red")
        and bio.nutrition_quality is not None
        and bio.nutrition_quality < 6
    ):
        recs.append("Prioritize a balanced meal today to support energy recovery.")
    if level == "red":
        recs.append("Hard stop at 10pm. No new work items today.")
    elif level == "yellow":
        recs.append("Hard stop at 11pm. Wind-down routine recommended.")
    return recs


class BioArchivistResult(AgentResult):
    status: BioStatus | None = None


class BioArchivist:
    """Computes burnout score from sleep, nutrition, and energy inputs."""

    async def process(
        self, payload: CheckInPayload, history: dict[str, Any] | None = None
    ) -> BioArchivistResult:
        """Compute burnout score from sleep, nutrition, and energy inputs.

        Combines the current check-in's bio fields with rolling history to
        calculate a weighted burnout score and cumulative sleep debt, then
        returns a BioStatus with forecast text and recovery recommendations.
        When no bio data is present and no history exists, returns an idle
        green status.

        Args:
            payload: Parsed check-in; payload.bio may be None.
            history: Optional dict containing "bio" key with a list of recent
                bio metric dicts for rolling debt calculation.

        Returns:
            BioArchivistResult with populated BioStatus and any triage items.
        """
        bio = payload.bio
        bio_history = (history.get("bio") if history else None) or []

        if bio is None:
            if not bio_history:
                return BioArchivistResult(
                    success=True,
                    status=BioStatus(
                        status="green",
                        burnout_score=0,
                        forecast="No data received. System monitoring idle.",
                    ),
                )
            bio = BioInput()

        score, debt = _compute_burnout(bio, bio_history)
        level = _burnout_status(score)

        triage: list[TriageItem] = []
        if level == "yellow":
            triage.append(
                TriageItem(
                    id="bio-temp-0",
                    priority=6,
                    domain="bio",
                    description=f"Burnout risk elevated (score {score:.0f}). Sleep debt: {debt}h.",
                    action="Schedule a hard stop at 11pm and set a bedtime alarm.",
                )
            )
        elif level == "red":
            triage.append(
                TriageItem(
                    id="bio-temp-0",
                    priority=9,
                    domain="bio",
                    description=f"Burnout risk critical (score {score:.0f}). Sleep debt: {debt}h.",
                    action="Hard stop at 10pm. No new work items today. Recovery is the priority.",
                )
            )

        return BioArchivistResult(
            status=BioStatus(
                status=level,
                burnout_score=score,
                forecast=_forecast(level, score),
                sleep_debt_hours=debt,
                recommendations=_recommendations(level, bio),
            ),
            triage_items=triage,
        )
