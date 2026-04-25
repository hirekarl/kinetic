from __future__ import annotations

import os

from google import genai

from kinetic.models.outputs import StatusLevel, TriageItem


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
    ) -> str:
        """Formulate a tactical feedback readout based on system state."""

        # Prepare context for the prompt
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

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                config={"system_instruction": system_prompt},
                contents=user_context,
            )
            return response.text or "Liaison offline. Proceed with baseline triage."
        except Exception as e:
            return f"[SYSTEM ERROR] Liaison processing failure: {e}"
