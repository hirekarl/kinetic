from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

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
    source_id: str | None = Field(
        default=None,
        description="Originating task name for logistics items; used for server-side completion",
    )


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


class BioTrend(BaseModel):
    avg_sleep_hours: float
    sleep_slope: float = Field(description="Negative = declining nightly, positive = improving")
    avg_nutrition: float
    avg_energy: float
    worst_sleep_day: str | None = Field(default=None, description='ISO date "YYYY-MM-DD"')
    days_analyzed: int
    sleep_series: list[float] = Field(
        default_factory=list,
        description="Per-day sleep hours, oldest→newest, same window as days_analyzed",
    )
    burnout_series: list[float] = Field(
        default_factory=list,
        description="Per-entry burnout score 0-100, oldest->newest, same window as days_analyzed",
    )


class RecurringTask(BaseModel):
    name: str
    times_overdue: int = Field(description="Count of check-ins where task appeared overdue")
    avg_days_overdue: float
    priority: str


class RelationalDrift(BaseModel):
    person: str
    contact_trend: float = Field(
        description="Avg daily increase in days_since_contact across check-ins"
    )
    avg_vibe_score: float
    last_known_days_since_contact: int


class BehavioralSummary(BaseModel):
    bio_trend: BioTrend | None = None
    recurring_tasks: list[RecurringTask] = Field(default_factory=list)
    relational_drifts: list[RelationalDrift] = Field(default_factory=list)
    days_analyzed: int
    generated_at: datetime


class BehavioralProfile(BaseModel):
    profile_key: str = Field(description='e.g. "sleep_deficit_pattern", "work_boundary_violation"')
    insight: str = Field(description="LLM-generated plain-language description of the pattern")
    evidence: dict[str, Any] = Field(description="Structured data points supporting the insight")
    first_observed: datetime
    last_updated: datetime
    observation_count: int


class ContactPause(BaseModel):
    person: str
    paused_until: date
    reason: str | None = None


class SystemHealthPayload(BaseModel):
    """Canonical output from the lead orchestrator, consumed directly by the frontend."""

    overall_status: StatusLevel
    bio: BioStatus | None = None
    logistics: LogisticsStatus | None = None
    relational: RelationalStatus | None = None
    triage_items: list[TriageItem] = Field(default_factory=list)
    roi_summary: ROISummary | None = None
    liaison_feedback: str | None = None
    responding_agent: str | None = None
    behavioral_profiles: list[BehavioralProfile] = Field(default_factory=list)
    behavioral_summary: BehavioralSummary | None = None
    active_pauses: list[ContactPause] = Field(default_factory=list)
