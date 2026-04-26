from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from kinetic.models.inputs import LogisticsTask

StatusLevel = Literal["green", "yellow", "red"]
AgentDomain = Literal["bio", "logistics", "relational", "system"]


class TriageItem(BaseModel):
    id: str
    priority: int = Field(ge=1, le=10, description="Higher = more urgent")
    domain: AgentDomain
    description: str
    action: str
    snooze_until: datetime | None = None
    completed: bool = False


class ROISummary(BaseModel):
    time_recovered_minutes: int = Field(ge=0)
    margin_recovered: str
    burnout_risk_delta: float = Field(description="Negative = improved, positive = worsened")


class BioStatus(BaseModel):
    status: StatusLevel
    burnout_score: float = Field(ge=0, le=100)
    forecast: str
    sleep_debt_hours: float = 0.0
    recommendations: list[str] = Field(default_factory=list)
    error_message: str | None = None


class LogisticsStatus(BaseModel):
    status: StatusLevel
    critical_tasks: list[str] = Field(default_factory=list)
    tasks_with_steps: list[LogisticsTask] = Field(default_factory=list)
    outsourcing_suggestions: list[str] = Field(default_factory=list)
    time_to_resolve_minutes: int = 0
    error_message: str | None = None


class RelationalStatus(BaseModel):
    status: StatusLevel
    connection_margin_score: float = Field(ge=0, le=100)
    at_risk_relationships: list[str] = Field(default_factory=list)
    interaction_sprints: list[str] = Field(default_factory=list)
    error_message: str | None = None


class SystemHealthPayload(BaseModel):
    """Canonical output from the lead orchestrator, consumed directly by the frontend."""

    overall_status: StatusLevel
    bio: BioStatus | None = None
    logistics: LogisticsStatus | None = None
    relational: RelationalStatus | None = None
    triage_items: list[TriageItem] = Field(default_factory=list)
    roi_summary: ROISummary | None = None
    liaison_feedback: str | None = None
