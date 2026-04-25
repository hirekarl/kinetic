from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LogisticsTask(BaseModel):
    name: str
    days_overdue: int = 0
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    notes: str | None = None


class VibeCheck(BaseModel):
    person: str
    score: int = Field(ge=1, le=10, description="Connection health 1-10")
    days_since_contact: int = Field(ge=0)
    notes: str | None = None


class BioInput(BaseModel):
    sleep_hours: float | None = Field(default=None, ge=0, le=24)
    nutrition_quality: int | None = Field(default=None, ge=1, le=10)
    energy_level: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = None


class LogisticsInput(BaseModel):
    tasks: list[LogisticsTask] = Field(default_factory=list)


class RelationalInput(BaseModel):
    vibe_checks: list[VibeCheck] = Field(default_factory=list)


class CheckInPayload(BaseModel):
    """Root input model parsed from a user's natural-language check-in message.

    All sub-models are Optional; None means the domain was not mentioned and
    the corresponding agent should be skipped.
    """

    bio: BioInput | None = None
    logistics: LogisticsInput | None = None
    relational: RelationalInput | None = None
