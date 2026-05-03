"""Unit tests for the LLM parsing layer."""

import os
from unittest.mock import MagicMock, patch

import pytest

from kinetic.models.inputs import CheckInPayload
from kinetic.parsing.llm_parser import parse_checkin


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_checkin_raises_oserror_if_key_missing() -> None:
    """Missing GEMINI_API_KEY raises OSError."""
    with (
        patch.dict(os.environ, {}, clear=True),
        pytest.raises(OSError, match="GEMINI_API_KEY is not set"),
    ):
        await parse_checkin("Slept well.")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_checkin_returns_payload_on_success() -> None:
    """Successful mock call returns a CheckInPayload."""
    mock_payload = CheckInPayload(
        bio={"sleep_hours": 8.0, "nutrition_quality": 9, "energy_level": 9}
    )

    # Mock instructor client and its chat.completions.create method
    mock_client = MagicMock()
    # For async calls, the return value should be an awaitable
    mock_client.chat.completions.create.return_value = mock_payload

    with (
        patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}),
        patch("instructor.from_genai", return_value=mock_client),
        patch("google.genai.Client"),
    ):
        result = await parse_checkin("Slept 8 hours, ate great, feeling energized.")

    assert isinstance(result, CheckInPayload)
    assert result.bio is not None
    assert result.bio.sleep_hours == 8.0
    assert result.bio.nutrition_quality == 9


@pytest.mark.unit
@pytest.mark.asyncio
async def test_parse_checkin_extends_messages_with_history() -> None:
    """When history is provided the messages list includes history entries before user message."""
    mock_payload = CheckInPayload()
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_payload

    history = [
        {"role": "user", "content": "Slept 5 hours."},
        {"role": "assistant", "content": "Noted."},
    ]

    with (
        patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key"}),
        patch("instructor.from_genai", return_value=mock_client),
        patch("google.genai.Client"),
    ):
        result = await parse_checkin("Slept 7 hours tonight.", history=history)

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    messages_sent = call_kwargs["messages"]
    contents = [m["content"] for m in messages_sent]
    assert "Slept 5 hours." in contents
    assert "Slept 7 hours tonight." in contents
    assert isinstance(result, CheckInPayload)
