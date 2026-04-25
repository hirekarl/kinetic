from __future__ import annotations

from kinetic.agents.base import AgentResult
from kinetic.models.inputs import CheckInPayload
from kinetic.models.outputs import RelationalStatus


class RelationalDiplomatResult(AgentResult):
    status: RelationalStatus | None = None


class RelationalDiplomat:
    """Tracks connection margin and recommends interaction sprints."""

    async def process(self, payload: CheckInPayload) -> RelationalDiplomatResult:
        raise NotImplementedError
