from __future__ import annotations

import os
from typing import cast

import google.generativeai as genai
import instructor

from kinetic.models.inputs import CheckInPayload


async def parse_checkin(message: str) -> CheckInPayload:
    """Parse a natural-language check-in message into a typed CheckInPayload.

    Uses Google Gemini 2.5 Flash via Instructor to enforce structured output.
    Requires GEMINI_API_KEY in the environment.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise OSError("GEMINI_API_KEY is not set")

    genai.configure(api_key=api_key)

    client = instructor.from_gemini(
        client=genai.GenerativeModel(
            model_name="models/gemini-2.5-flash",
        ),
        mode=instructor.Mode.GEMINI_JSON,
    )

    return cast(
        CheckInPayload,
        client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the Kinetic LLM Parser. Your job is to extract bio-metrics, "
                        "logistics tasks, and relational vibe checks from user messages into "
                        "a structured JSON format. If a domain is not mentioned, return null for it."
                    ),
                },
                {"role": "user", "content": message},
            ],
            response_model=CheckInPayload,
        ),
    )
