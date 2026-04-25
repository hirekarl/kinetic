from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from kinetic.models.inputs import CheckInPayload


class AgentResult(BaseModel):
    """Base result returned by every agent. Subclassed by each agent."""

    success: bool = True
    error_message: str | None = None


@runtime_checkable
class Agent(Protocol):
    """Structural protocol all Kinetic agents must satisfy."""

    async def process(self, payload: CheckInPayload) -> AgentResult: ...
