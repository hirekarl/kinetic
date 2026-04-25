from __future__ import annotations

from kinetic.agents.base import AgentResult
from kinetic.models.inputs import CheckInPayload
from kinetic.models.outputs import BioStatus


class BioArchivistResult(AgentResult):
    status: BioStatus | None = None


class BioArchivist:
    """Tracks sleep/nutrition data and computes burnout forecast."""

    async def process(self, payload: CheckInPayload) -> BioArchivistResult:
        raise NotImplementedError
