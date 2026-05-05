from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from typing import Any, Literal

import instructor
import structlog
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from kinetic.agents.liaison_context import (
    format_behavioral_summary,
    format_bio_status,
    format_logistics_status,
    format_profiles,
    format_relational_status,
)
from kinetic.models.outputs import (
    BehavioralProfile,
    BehavioralSummary,
    BioStatus,
    LogisticsStatus,
    RelationalStatus,
    StatusLevel,
    TriageItem,
)

log = structlog.get_logger()

_MODEL = "gemini-2.5-flash"
_HISTORY_WINDOW = 10  # max prior messages forwarded to the LLM
_METADATA_KEYWORDS: frozenset[str] = frozenset(
    {"pause", "break", "no contact", "done with", "completed", "finished"}
)

RespondingAgent = Literal["liaison", "bio_archivist", "logistics_fixer", "relational_diplomat"]


class ContactPauseDirective(BaseModel):
    person: str = Field(description="Full name of the contact to pause outreach for")
    pause_days: int = Field(ge=1, le=365, description="Number of days to pause contact")
    reason: str | None = Field(default=None, description="Brief reason for the pause")


class LiaisonMetadata(BaseModel):
    """Lightweight metadata extracted after streaming — responding agent and side-effect directives."""

    responding_agent: RespondingAgent = "liaison"
    contact_pauses: list[ContactPauseDirective] = Field(default_factory=list)
    task_completions: list[str] = Field(default_factory=list)


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
        self._raw_client = genai.Client(api_key=api_key)
        self.client = instructor.from_genai(
            client=self._raw_client,
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
        _, messages = self._build_prompt_parts(
            message=message,
            overall_status=overall_status,
            triage_items=triage_items,
            behavioral_summary=behavioral_summary,
            behavioral_profiles=behavioral_profiles,
            history=history,
            bio_status=bio_status,
            logistics_status=logistics_status,
            relational_status=relational_status,
        )
        # Gemini requires "model" role; Instructor does not translate "assistant" automatically
        gemini_messages = [
            {**msg, "role": "model" if msg["role"] == "assistant" else msg["role"]}
            for msg in messages
        ]
        log.info("llm.call.start", model=_MODEL)
        try:
            result = LiaisonResponse.model_validate(
                self.client.chat.completions.create(
                    model=_MODEL,
                    messages=gemini_messages,
                    response_model=LiaisonResponse,
                ).model_dump()
            )
            log.info("llm.call.done", model=_MODEL)
            return result
        except Exception as e:
            log.error("llm.call.error", model=_MODEL, exc=str(e))
            return LiaisonResponse(text=f"[SYSTEM ERROR] Liaison processing failure: {e}")

    def _build_prompt_parts(
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
    ) -> tuple[str, list[dict[str, Any]]]:
        """Return (system_prompt, openai_style_messages) for use by process() and stream_text()."""
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
            "name and the number of days. ONLY for explicit no-contact requests.\n\n"
            "TASK COMPLETION RULE:\n"
            "10. If the user explicitly states they completed or finished a specific task, populate "
            "task_completions with the exact task name(s). ONLY for explicit completion statements.\n\n"
            "SITUATIONAL AWARENESS RULES:\n"
            "11. SYNTHESIS — When multiple domains are simultaneously RED or critical (competing crisis), "
            "do not respond domain-by-domain. Produce a single unified sequenced protocol: triage the "
            "most acute risk first, then chain the remaining domains in order of urgency.\n"
            "12. IMPROVEMENT ACK — When the user reports partial improvement (slept better, finished "
            "a task, made contact), explicitly acknowledge the delta from prior status, update the "
            "forecast, and rebalance recommendations to reflect the new baseline.\n"
            "13. EVENT ROUTING — When the user mentions an upcoming deadline or event, activate all "
            "three specialists: Bio Archivist gives pre-event energy protocol, Logistics Fixer clears "
            "the queue, Relational Diplomat handles any social commitments. One action per domain.\n"
            "14. HISTORY RESOLUTION — When the user uses pronouns (he, she, they, it) or vague "
            "references, resolve the referent from the last 3 conversation turns before responding. "
            "Never ask for clarification if context resolves it.\n"
            "15. AGENCY — If the user explicitly overrides a prior recommendation (states they will "
            "proceed against advice), do not re-argue the point. Pivot immediately to risk mitigation: "
            "what can be done to reduce harm given the chosen path."
        )
        system_context = (
            f"OVERALL SYSTEM STATUS: {overall_status.upper()}\n"
            f"TRIAGE ITEMS:\n{triage_summary if triage_items else 'All systems nominal.'}"
        )
        if bio_status is not None:
            system_context += format_bio_status(bio_status)
        if logistics_status is not None:
            system_context += format_logistics_status(logistics_status)
        if relational_status is not None:
            system_context += format_relational_status(relational_status)
        if behavioral_summary is not None:
            system_context += format_behavioral_summary(behavioral_summary)
        if behavioral_profiles:
            system_context += format_profiles(behavioral_profiles)

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
        return system_prompt, messages

    async def stream_text(
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
    ) -> AsyncGenerator[str, None]:
        """Yield raw text chunks from Gemini streaming using the same prompt as process()."""
        system_prompt, openai_messages = self._build_prompt_parts(
            message=message,
            overall_status=overall_status,
            triage_items=triage_items,
            behavioral_summary=behavioral_summary,
            behavioral_profiles=behavioral_profiles,
            history=history,
            bio_status=bio_status,
            logistics_status=logistics_status,
            relational_status=relational_status,
        )
        # Convert OpenAI-style messages to genai content format (skip system → system_instruction)
        genai_contents: list[types.Content] = []
        for msg in openai_messages:
            if msg["role"] == "system":
                continue
            role = "user" if msg["role"] == "user" else "model"
            genai_contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

        config = types.GenerateContentConfig(system_instruction=system_prompt)
        log.info("llm.stream.start", model=_MODEL)
        stream = await self._raw_client.aio.models.generate_content_stream(
            model=_MODEL,
            contents=genai_contents,
            config=config,
        )
        async for chunk in stream:
            if chunk.text:
                yield chunk.text
        log.info("llm.stream.done", model=_MODEL)

    async def extract_metadata(self, streamed_text: str, message: str) -> LiaisonMetadata:
        """Extract responding_agent / contact_pauses / task_completions from streamed text.

        Skips the Instructor call entirely when the message contains no relevant keywords,
        avoiding an extra round-trip for the common case of a plain check-in message.
        """
        if not any(kw in message.lower() for kw in _METADATA_KEYWORDS):
            return LiaisonMetadata()
        log.info("llm.metadata.start", model=_MODEL)
        try:
            result = LiaisonMetadata.model_validate(
                self.client.chat.completions.create(
                    model=_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                "Extract structured metadata from the following liaison exchange.\n\n"
                                f"User message: {message}\n\n"
                                f"Liaison response: {streamed_text}"
                            ),
                        }
                    ],
                    response_model=LiaisonMetadata,
                ).model_dump()
            )
            log.info("llm.metadata.done", model=_MODEL)
            return result
        except Exception:
            return LiaisonMetadata()
