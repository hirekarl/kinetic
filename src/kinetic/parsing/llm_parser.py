from __future__ import annotations

import os
from typing import cast

import instructor
from google import genai

from kinetic.models.inputs import CheckInPayload


async def parse_checkin(
    message: str, history: list[dict[str, str]] | None = None
) -> CheckInPayload:
    """Parse a natural-language check-in message into a typed CheckInPayload.

    Uses Google Gemini 2.5 Flash via Instructor to enforce structured output.
    Requires GEMINI_API_KEY in the environment.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise OSError("GEMINI_API_KEY is not set")

    client = instructor.from_genai(
        client=genai.Client(api_key=api_key),
        mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS,
    )

    system_content = (
        "You are the Kinetic LLM Parser. Your job is to extract bio-metrics, "
        "logistics tasks, and relational vibe checks from user messages into "
        "a structured JSON format. If a domain is not mentioned, return null for it.\n\n"
        "LOGISTICS RULES:\n"
        "1. If a new logistics task is mentioned, break it down into 3-5 specific, "
        "actionable micro-steps in the 'subtasks' field.\n"
        "2. If the user indicates they completed a specific substep or the current task "
        "(e.g., 'I did it', 'Done with the sock'), add that specific text to 'completed_subtasks'.\n"
        "3. Only set 'status' to 'completed' if the ENTIRE task is clearly finished."
    )

    messages = [{"role": "system", "content": system_content}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    return cast(
        CheckInPayload,
        client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=messages,
            response_model=CheckInPayload,
        ),
    )
