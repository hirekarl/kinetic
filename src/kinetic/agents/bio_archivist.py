from __future__ import annotations

from kinetic.agents.base import AgentResult
from kinetic.models.inputs import BioInput, CheckInPayload
from kinetic.models.outputs import BioStatus, StatusLevel, TriageItem

_SLEEP_WEIGHT = 0.4
_NUTRITION_WEIGHT = 0.3
_ENERGY_WEIGHT = 0.3
_BASELINE_SLEEP_HOURS = 8.0
_SLEEP_PENALTY_PER_HOUR = 25.0  # 4h deficit → score 100


def _sleep_component(sleep_hours: float) -> float:
    deficit = max(0.0, _BASELINE_SLEEP_HOURS - sleep_hours)
    return min(100.0, deficit * _SLEEP_PENALTY_PER_HOUR)


def _nutrition_component(quality: int) -> float:
    return (10 - quality) / 9.0 * 100.0


def _energy_component(level: int) -> float:
    return (10 - level) / 9.0 * 100.0


def _burnout_status(score: float) -> StatusLevel:
    if score < 40:
        return "green"
    if score < 70:
        return "yellow"
    return "red"


def _compute_burnout(bio: BioInput) -> tuple[float, float]:
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
    debt = round(max(0.0, _BASELINE_SLEEP_HOURS - (bio.sleep_hours or _BASELINE_SLEEP_HOURS)), 2)
    return score, debt


def _forecast(level: StatusLevel, score: float) -> str:
    if level == "green":
        return f"Low burnout risk (score {score:.0f}). Recovery margin healthy."
    if level == "yellow":
        return f"Moderate burnout risk (score {score:.0f}). Hard stop by 11pm recommended."
    return f"High burnout risk (score {score:.0f}). Recovery actions needed today."


def _recommendations(level: StatusLevel, bio: BioInput) -> list[str]:
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

    async def process(self, payload: CheckInPayload) -> BioArchivistResult:
        if payload.bio is None:
            return BioArchivistResult(success=False, error_message="No bio data in payload.")

        bio = payload.bio
        score, debt = _compute_burnout(bio)
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
