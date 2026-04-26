from __future__ import annotations

import os
from typing import Any, Literal

import instructor
from google import genai
from pydantic import BaseModel, Field

from kinetic.models.outputs import (
    BehavioralProfile,
    BehavioralSummary,
    BioStatus,
    LogisticsStatus,
    RelationalStatus,
    StatusLevel,
    TriageItem,
)

_HISTORY_WINDOW = 10  # max prior messages forwarded to the LLM

RespondingAgent = Literal["liaison", "bio_archivist", "logistics_fixer", "relational_diplomat"]


class ContactPauseDirective(BaseModel):
    person: str = Field(description="Full name of the contact to pause outreach for")
    pause_days: int = Field(ge=1, le=365, description="Number of days to pause contact")
    reason: str | None = Field(default=None, description="Brief reason for the pause")


class LiaisonResponse(BaseModel):
    text: str = Field(description="Response text shown to the user")
    responding_agent: RespondingAgent = Field(
        default="liaison",
        description=(
            "Which specialist is responding. Set to 'bio_archivist' for health/sleep/burnout, "
            "'logistics_fixer' for tasks/priorities/deadlines, "
            "'relational_diplomat' for relationships/contacts, "
            "'liaison' for general or cross-domain responses."
        ),
    )
    contact_pauses: list[ContactPauseDirective] = Field(
        default_factory=list,
        description=(
            "Populate ONLY when the user explicitly states a no-contact agreement, relationship "
            "break, or contact pause for a specific person. Leave empty for everything else."
        ),
    )
    task_completions: list[str] = Field(
        default_factory=list,
        description=(
            "Populate with task names ONLY when the user explicitly states they completed or "
            "finished a specific task. Each entry must match an exact task name from the triage "
            "list. Leave empty for all other messages."
        ),
    )


class OperationalLiaison:
    """Routes user messages to specialist agents and mediates their responses."""

    def __init__(self, api_key: str | None = None) -> None:
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise OSError("GEMINI_API_KEY is not set for OperationalLiaison")
        self.client = instructor.from_genai(
            client=genai.Client(api_key=api_key),
            mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS,
        )

    async def process(
        self,
        message: str,
        overall_status: StatusLevel,
        triage_items: list[TriageItem],
        behavioral_summary: BehavioralSummary | None = None,
        behavioral_profiles: list[BehavioralProfile] | None = None,
        history: list[dict[str, str]] | None = None,
        bio_status: BioStatus | None = None,
        logistics_status: LogisticsStatus | None = None,
        relational_status: RelationalStatus | None = None,
    ) -> LiaisonResponse:
        """Route message to the appropriate specialist and return a structured response."""
        triage_summary = "\n".join(
            [f"- [{item.priority}] {item.description}: {item.action}" for item in triage_items]
        )

        system_prompt = (
            "You are the Operational Liaison for a high-performance engineer running Kinetic, "
            "a personal infrastructure system staffed by three specialist agents:\n"
            "  • Bio Archivist — health, sleep, nutrition, burnout, energy\n"
            "  • Logistics Fixer — tasks, priorities, outsourcing ROI, deadlines\n"
            "  • Relational Diplomat — relationship health, connection margin, outreach timing\n\n"
            "ROUTING RULES:\n"
            "1. If the user addresses a specialist by name/role or asks a question clearly within "
            "one domain, set responding_agent to that specialist and answer in their expert voice.\n"
            "2. For general or cross-domain questions, you (liaison) answer.\n"
            "3. Each specialist speaks with domain authority: Bio Archivist gives clinical health "
            "guidance; Logistics Fixer gives operational prioritization; Relational Diplomat gives "
            "measured connection strategy.\n\n"
            "RESPONSE RULES:\n"
            "4. Read the user's intent. Answer the actual question using system data as context — "
            "do not just echo the status level.\n"
            "5. For goals or plans (recover burnout, prep for event, repair a relationship), give "
            "a concrete 2-4 step action plan.\n"
            "6. When status is RED or YELLOW, you may authorize dropping non-critical tasks — "
            "only after addressing the question.\n"
            "7. TONE: Direct, tactical, domain-expert. No emotional preamble.\n"
            "8. LENGTH: 1-2 sentences for data briefs; 3-5 sentences with numbered steps for plans.\n\n"
            "CONTACT PAUSE RULE:\n"
            "9. If the user explicitly states a no-contact agreement, relationship break, or asks "
            "to pause outreach for a specific person, populate contact_pauses with the person's "
            "name and the number of days. ONLY for explicit no-contact requests."
        )

        system_context = (
            f"OVERALL SYSTEM STATUS: {overall_status.upper()}\n"
            f"TRIAGE ITEMS:\n{triage_summary if triage_items else 'All systems nominal.'}"
        )
        if bio_status is not None:
            system_context += _format_bio_status(bio_status)
        if logistics_status is not None:
            system_context += _format_logistics_status(logistics_status)
        if relational_status is not None:
            system_context += _format_relational_status(relational_status)
        if behavioral_summary is not None:
            system_context += _format_behavioral_summary(behavioral_summary)
        if behavioral_profiles:
            system_context += _format_profiles(behavioral_profiles)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"[SYSTEM CONTEXT]\n{system_context}"},
            {"role": "assistant", "content": "Context received. Ready for briefing."},
        ]
        if history:
            for msg in history[-_HISTORY_WINDOW:]:
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        try:
            return LiaisonResponse.model_validate(
                self.client.chat.completions.create(
                    model="gemini-2.5-flash",
                    messages=messages,
                    response_model=LiaisonResponse,
                ).model_dump()
            )
        except Exception as e:
            return LiaisonResponse(text=f"[SYSTEM ERROR] Liaison processing failure: {e}")


# ── Context formatters ────────────────────────────────────────────────────────


def _format_bio_status(bio: BioStatus) -> str:
    lines = ["\n\nBIO ARCHIVIST — Current Status:"]
    lines.append(
        f"Burnout: {bio.burnout_score:.0f}/100 | Sleep Debt: {bio.sleep_debt_hours:.1f}h | Status: {bio.status.upper()}"
    )
    if bio.forecast:
        lines.append(f"Forecast: {bio.forecast}")
    if bio.recommendations:
        lines.append("Recommendations: " + "; ".join(bio.recommendations))
    return "\n".join(lines)


def _format_logistics_status(logistics: LogisticsStatus) -> str:
    lines = ["\n\nLOGISTICS FIXER — Current Status:"]
    lines.append(
        f"Status: {logistics.status.upper()} | Queue clearance: {logistics.time_to_resolve_minutes}min"
    )
    if logistics.critical_tasks:
        lines.append("Critical: " + ", ".join(logistics.critical_tasks))
    if logistics.tasks_with_steps:
        for t in logistics.tasks_with_steps:
            steps = ", ".join(t.subtasks) if t.subtasks else "no steps defined"
            lines.append(f"  • {t.name} [{t.priority}]: {steps}")
    if logistics.outsourcing_suggestions:
        lines.append("Outsource candidates: " + "; ".join(logistics.outsourcing_suggestions))
    return "\n".join(lines)


def _format_relational_status(relational: RelationalStatus) -> str:
    lines = ["\n\nRELATIONAL DIPLOMAT — Current Status:"]
    lines.append(
        f"Status: {relational.status.upper()} | Connection Margin: {relational.connection_margin_score:.0f}/100"
    )
    if relational.at_risk_relationships:
        lines.append("At-risk: " + ", ".join(relational.at_risk_relationships))
    if relational.interaction_sprints:
        lines.append("Sprints: " + "; ".join(relational.interaction_sprints))
    return "\n".join(lines)


def _format_behavioral_summary(summary: BehavioralSummary) -> str:
    lines = ["\n\nBEHAVIORAL CONTEXT (14-day trend):"]
    if summary.bio_trend:
        bt = summary.bio_trend
        lines.append(
            f"Sleep: avg {bt.avg_sleep_hours:.1f} hrs/night, "
            f"trend {bt.sleep_slope:+.2f} hrs/day over {bt.days_analyzed} days"
        )
        lines.append(f"Nutrition: {bt.avg_nutrition:.1f}/10 | Energy: {bt.avg_energy:.1f}/10")
        if bt.worst_sleep_day:
            lines.append(f"Worst sleep: {bt.worst_sleep_day}")
    if summary.recurring_tasks:
        lines.append(
            "Recurring overdue: "
            + ", ".join(f"{t.name} ({t.times_overdue}x)" for t in summary.recurring_tasks)
        )
    if summary.relational_drifts:
        lines.append(
            "Drifting contacts: "
            + ", ".join(
                f"{d.person} (+{d.contact_trend:.1f}d/check-in)" for d in summary.relational_drifts
            )
        )
    return "\n".join(lines)


def _format_profiles(profiles: list[BehavioralProfile]) -> str:
    lines = ["\n\nESTABLISHED BEHAVIORAL PATTERNS:"]
    for p in profiles:
        lines.append(f"- {p.profile_key}: {p.insight} (observed {p.observation_count}x)")
    return "\n".join(lines)
