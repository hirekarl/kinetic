from __future__ import annotations

from kinetic.agents.base import AgentResult
from kinetic.models.inputs import CheckInPayload
from kinetic.models.outputs import LogisticsStatus


class LogisticsFixerResult(AgentResult):
    status: LogisticsStatus | None = None


class LogisticsFixer:
    """Triages domestic tasks and surfaces outsourcing ROI recommendations."""

    async def process(self, payload: CheckInPayload) -> LogisticsFixerResult:
        raise NotImplementedError
