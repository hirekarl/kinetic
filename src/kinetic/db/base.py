from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from kinetic.models.inputs import CheckInPayload
from kinetic.models.outputs import BehavioralProfile, BehavioralSummary


@runtime_checkable
class DatabaseClient(Protocol):  # pragma: no cover
    """Shared persistence interface satisfied by both SqliteClient and PostgresClient.

    All methods are async.  Implementations must provide per-tenant row isolation;
    the concrete client is responsible for scoping every query to the correct tenant.
    """

    async def insert_checkin(
        self, payload: CheckInPayload, message: str, liaison_feedback: str | None = None
    ) -> str:
        """Persist a parsed check-in and return the new check-in UUID.

        Args:
            payload: The fully-parsed CheckInPayload, including bio/logistics/relational.
            message: The raw user message text.
            liaison_feedback: The Operational Liaison's response text, if available.

        Returns:
            The UUID string assigned to the newly created check-in row.
        """
        ...

    async def insert_checkin_at(
        self,
        payload: CheckInPayload,
        message: str,
        timestamp: datetime,
        liaison_feedback: str | None = None,
    ) -> str:
        """Persist a check-in with an explicit timestamp and return the new UUID.

        Identical to insert_checkin() but uses the caller-supplied timestamp
        instead of the current time.  Used by the simulation service to
        backfill historical data.

        Args:
            payload: The fully-parsed CheckInPayload.
            message: The raw user message text.
            timestamp: The datetime to record for this check-in.
            liaison_feedback: The Operational Liaison's response text, if available.

        Returns:
            The UUID string assigned to the newly created check-in row.
        """
        ...

    async def get_latest_bio(self) -> dict[str, Any] | None:
        """Return the most recent bio metrics row, or None if no data exists.

        Returns:
            Dict with keys sleep_hours, nutrition_quality, energy_level, or None.
        """
        ...

    async def get_all_tasks(self) -> list[dict[str, Any]]:
        """Return all tasks with their latest days_overdue value from check-in history.

        Returns:
            List of task dicts with keys: name, priority, subtasks,
            completed_subtasks, status, days_overdue.
        """
        ...

    async def get_all_vibes(self) -> list[dict[str, Any]]:
        """Return the most recent vibe check for each distinct person.

        Returns:
            List of dicts with keys: person, score, days_since_contact.
        """
        ...

    async def get_recent_bio(self, limit: int = 7) -> list[dict[str, Any]]:
        """Return the most recent bio metric rows, newest first.

        Args:
            limit: Maximum number of rows to return.

        Returns:
            List of dicts with keys: sleep_hours, nutrition_quality, energy_level.
        """
        ...

    async def upsert_contact_pause(
        self, person: str, paused_until: str, reason: str | None
    ) -> None:
        """Insert or update a contact pause record keyed by person name.

        Args:
            person: The contact's name (primary key).
            paused_until: ISO date string (YYYY-MM-DD) through which the pause is active.
            reason: Optional free-text reason for the pause.
        """
        ...

    async def get_active_pauses(self) -> list[dict[str, Any]]:
        """Return contact pauses whose paused_until date is today or later.

        Returns:
            List of dicts with keys: person, paused_until, reason.
        """
        ...

    async def get_history(self, limit: int = 20) -> list[dict[str, str]]:
        """Return interleaved user and system messages for conversation hydration.

        Args:
            limit: Maximum number of check-in rows to include.

        Returns:
            Ordered list of {"role": "user"|"system", "content": str} dicts.
        """
        ...

    async def get_behavioral_summary(self, days: int = 14) -> BehavioralSummary:
        """Compute a structured behavioral summary from the last N days of check-ins.

        Args:
            days: Look-back window in days.

        Returns:
            BehavioralSummary with bio trend, recurring tasks, and relational drifts.
        """
        ...

    async def get_behavioral_profiles(self) -> list[BehavioralProfile]:
        """Return all accumulated behavioral profiles, newest-updated first.

        Returns:
            List of BehavioralProfile objects.
        """
        ...

    async def upsert_behavioral_profile(self, profile: BehavioralProfile) -> None:
        """Insert or update a behavioral profile.

        The first_observed timestamp is never overwritten on conflict.

        Args:
            profile: The BehavioralProfile to persist.
        """
        ...

    async def complete_task(self, task_name: str) -> None:
        """Mark a task as completed.

        Args:
            task_name: The name of the task to complete.

        Raises:
            KeyError: If no task with the given name exists.
        """
        ...

    async def complete_subtask(self, task_name: str, subtask_name: str) -> None:
        """Append subtask_name to completed_subtasks for the named task.

        Auto-completes the parent task when all subtasks are in completed_subtasks
        (only when the subtasks list is non-empty).

        Args:
            task_name: The name of the parent task.
            subtask_name: The subtask step to mark complete.

        Raises:
            KeyError: If no task with task_name exists.
            ValueError: If subtask_name is not in the task's subtasks list.
        """
        ...

    async def clear_database(self) -> None:
        """Delete all data for the current tenant.  Irreversible."""
        ...

    async def get_burnout_series(self, days: int = 14) -> list[float]:
        """Return per-entry burnout scores for the last N days, oldest first.

        Args:
            days: Look-back window in days.

        Returns:
            List of burnout scores (0-100) in chronological order.
        """
        ...
