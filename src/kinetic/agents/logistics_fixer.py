from __future__ import annotations

from typing import Any

from kinetic.agents.base import AgentResult
from kinetic.models.inputs import CheckInPayload, LogisticsTask
from kinetic.models.outputs import LogisticsStatus, StatusLevel, TriageItem

_PRIORITY_WEIGHTS: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

_OUTSOURCING_HINTS: dict[str, str] = {
    "laundry": "Laundry pickup service: ~$25, saves 2h",
    "groceries": "Grocery delivery: ~$10 tip, saves 1h",
    "cleaning": "House cleaning service: ~$80, saves 3h",
    "dishes": "Paper plates short-term to clear the overhead",
    "dry cleaning": "Drop-off dry cleaning: ~$15, saves 45min",
}

_YELLOW_THRESHOLD = 6
_RED_THRESHOLD = 6  # criticality > _RED_THRESHOLD → red


def _criticality(task: LogisticsTask) -> int:
    return task.days_overdue * _PRIORITY_WEIGHTS.get(task.priority, 2)


def _task_level(score: int) -> StatusLevel:
    if score == 0:
        return "green"
    if score <= _YELLOW_THRESHOLD:
        return "yellow"
    return "red"


def _outsourcing_suggestion(task_name: str) -> str | None:
    name_lower = task_name.lower()
    for keyword, hint in _OUTSOURCING_HINTS.items():
        if keyword in name_lower:
            return hint
    return None


class LogisticsFixerResult(AgentResult):
    status: LogisticsStatus | None = None


class LogisticsFixer:
    """Triages domestic tasks and surfaces outsourcing ROI recommendations."""

    async def process(
        self, payload: CheckInPayload, history: dict[str, Any] | None = None
    ) -> LogisticsFixerResult:
        if payload.logistics is None:
            return LogisticsFixerResult(
                success=False, error_message="No logistics data in payload."
            )

        tasks = payload.logistics.tasks
        if not tasks:
            return LogisticsFixerResult(
                status=LogisticsStatus(
                    status="green",
                    critical_tasks=[],
                    outsourcing_suggestions=[],
                    time_to_resolve_minutes=0,
                )
            )

        overall: StatusLevel = "green"
        critical_tasks: list[str] = []
        outsourcing_suggestions: list[str] = []
        time_minutes = 0
        triage: list[TriageItem] = []

        for task in tasks:
            score = _criticality(task)
            level = _task_level(score)

            if level == "green":
                continue

            critical_tasks.append(task.name)
            weight = _PRIORITY_WEIGHTS.get(task.priority, 2)
            time_minutes += weight * 15

            suggestion = _outsourcing_suggestion(task.name)
            if suggestion:
                outsourcing_suggestions.append(suggestion)

            if level == "red":
                overall = "red"
                triage.append(
                    TriageItem(
                        id="logistics-temp-0",
                        priority=8,
                        domain="logistics",
                        description=f"{task.name} critically overdue ({task.days_overdue}d, {task.priority} priority).",
                        action=suggestion or f"Handle {task.name} today — blocking other recovery.",
                    )
                )
            elif level == "yellow" and overall != "red":
                overall = "yellow"
                triage.append(
                    TriageItem(
                        id="logistics-temp-0",
                        priority=5,
                        domain="logistics",
                        description=f"{task.name} overdue ({task.days_overdue}d, {task.priority} priority).",
                        action=suggestion or f"Schedule {task.name} within 24h.",
                    )
                )

        return LogisticsFixerResult(
            status=LogisticsStatus(
                status=overall,
                critical_tasks=critical_tasks,
                outsourcing_suggestions=outsourcing_suggestions,
                time_to_resolve_minutes=time_minutes,
            ),
            triage_items=triage,
        )
