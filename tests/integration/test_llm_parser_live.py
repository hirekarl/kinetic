"""Integration tests for the LLM parsing layer (requires GEMINI_API_KEY)."""

import os

import pytest

from kinetic.models.inputs import CheckInPayload
from kinetic.parsing.llm_parser import parse_checkin


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
async def test_parse_checkin_live() -> None:
    """Live integration test for parse_checkin.

    This test actually calls the Gemini API. Use sparingly.
    """
    message = (
        "Slept 7.5 hours, ate okay. "
        "Laundry is 2 days overdue and it's high priority. "
        "Marcus vibe check: 8/10, saw him 2 days ago."
    )
    result = await parse_checkin(message)

    assert isinstance(result, CheckInPayload)
    assert result.bio is not None
    assert result.bio.sleep_hours == 7.5

    assert result.logistics is not None
    assert len(result.logistics.tasks) > 0
    laundry = next((t for t in result.logistics.tasks if "laundry" in t.name.lower()), None)
    assert laundry is not None
    assert laundry.days_overdue == 2
    assert laundry.priority == "high"

    assert result.relational is not None
    marcus = next((v for v in result.relational.vibe_checks if "marcus" in v.person.lower()), None)
    assert marcus is not None
    assert marcus.score == 8
    assert marcus.days_since_contact == 2
