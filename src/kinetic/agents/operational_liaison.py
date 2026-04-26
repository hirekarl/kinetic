from __future__ import annotations

import os

from google import genai

from kinetic.models.outputs import BehavioralProfile, BehavioralSummary, StatusLevel, TriageItem


class OperationalLiaison:
    """Provides clinical, tactical micro-tasking to break decision paralysis."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise OSError("GEMINI_API_KEY is not set for OperationalLiaison")
        self.client = genai.Client(api_key=self.api_key)

    async def process(
        self,
        message: str,
        overall_status: StatusLevel,
        triage_items: list[TriageItem],
        behavioral_summary: BehavioralSummary | None = None,
        behavioral_profiles: list[BehavioralProfile] | None = None,
    ) -> str:
        """Formulate a tactical feedback readout based on system state."""
        triage_summary = "\n".join(
            [f"- [{item.priority}] {item.description}: {item.action}" for item in triage_items]
        )

        system_prompt = (
            "You are an Operational Liaison for a high-performance engineer. "
            "Your goal is to break decision paralysis and manage executive function burnout.\n\n"
            "TONE: Clinical, tactical, procedural (Military/NOC style). No emotional preamble. "
            "Maximum reduction of cognitive load.\n\n"
            "RULES:\n"
            "1. If system status is RED or YELLOW, explicitly authorize the user to drop non-critical tasks.\n"
            "2. Break down the highest-priority triage item into a single, micro-step instruction.\n"
            "3. Keep responses under 3 sentences."
        )

        user_context = (
            f"USER MESSAGE: {message}\n"
            f"SYSTEM STATUS: {overall_status.upper()}\n"
            f"TRIAGE ITEMS:\n{triage_summary if triage_items else 'All systems nominal.'}"
        )

        if behavioral_summary is not None:
            user_context += _format_summary(behavioral_summary)

        if behavioral_profiles:
            user_context += _format_profiles(behavioral_profiles)

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                config={"system_instruction": system_prompt},
                contents=user_context,
            )
            return response.text or "Liaison offline. Proceed with baseline triage."
        except Exception as e:
            return f"[SYSTEM ERROR] Liaison processing failure: {e}"


def _format_summary(summary: BehavioralSummary) -> str:
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
