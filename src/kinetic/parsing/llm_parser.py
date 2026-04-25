from __future__ import annotations

import os

from kinetic.models.inputs import CheckInPayload


async def parse_checkin(message: str) -> CheckInPayload:
    """Parse a natural-language check-in message into a typed CheckInPayload.

    Uses Google Gemini 2.5 Flash via Instructor to enforce structured output.
    Requires GEMINI_API_KEY in the environment.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise OSError("GEMINI_API_KEY is not set")

    # Implementation: Phase 2 (Agent Logic + LLM Parsing Layer)
    # Will use: instructor.from_gemini(genai.GenerativeModel("gemini-2.5-flash"))
    raise NotImplementedError
