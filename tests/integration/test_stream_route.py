"""Integration tests for POST /api/checkin/stream SSE endpoint."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from kinetic.auth import get_current_tenant
from kinetic.main import app
from kinetic.models.inputs import CheckInPayload
from kinetic.models.outputs import SystemHealthPayload

client = TestClient(app)


@pytest.fixture(autouse=True)
def bypass_auth() -> Generator[None, None, None]:
    app.dependency_overrides[get_current_tenant] = lambda: "test"
    yield
    app.dependency_overrides.pop(get_current_tenant, None)


async def _simple_stream() -> AsyncGenerator[dict[str, str], None]:
    health = SystemHealthPayload(overall_status="green")
    yield {"event": "agents", "data": health.model_dump_json()}
    yield {"event": "token", "data": json.dumps({"text": "Hello"})}
    yield {"event": "token", "data": json.dumps({"text": " world"})}
    yield {
        "event": "done",
        "data": json.dumps(
            {
                "responding_agent": "liaison",
                "contact_pauses": [],
                "task_completions": [],
                "active_pauses": [],
                "behavioral_profiles": [],
                "behavioral_summary": None,
            }
        ),
    }


@pytest.mark.unit
def test_stream_endpoint_empty_message_returns_400() -> None:
    """POST /api/checkin/stream with empty message returns 400 before streaming starts."""
    response = client.post("/api/checkin/stream", json={"message": ""})
    assert response.status_code == 400
    assert "message must not be empty" in response.json()["detail"]


@pytest.mark.unit
def test_stream_endpoint_returns_event_stream_content_type() -> None:
    """POST /api/checkin/stream returns text/event-stream content-type."""
    with (
        patch(
            "kinetic.api.routes.parse_checkin",
            new_callable=AsyncMock,
            return_value=CheckInPayload(),
        ),
        patch(
            "kinetic.api.routes.orchestrate_stream",
            return_value=_simple_stream(),
        ),
    ):
        response = client.post("/api/checkin/stream", json={"message": "Slept 7 hours."})

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.unit
def test_stream_endpoint_body_contains_agents_event() -> None:
    """POST /api/checkin/stream response body contains 'event: agents'."""
    with (
        patch(
            "kinetic.api.routes.parse_checkin",
            new_callable=AsyncMock,
            return_value=CheckInPayload(),
        ),
        patch(
            "kinetic.api.routes.orchestrate_stream",
            return_value=_simple_stream(),
        ),
    ):
        response = client.post("/api/checkin/stream", json={"message": "Check-in."})

    assert response.status_code == 200
    assert "event: agents" in response.text


@pytest.mark.unit
def test_stream_endpoint_body_contains_token_events() -> None:
    """POST /api/checkin/stream response body contains 'event: token' entries."""
    with (
        patch(
            "kinetic.api.routes.parse_checkin",
            new_callable=AsyncMock,
            return_value=CheckInPayload(),
        ),
        patch(
            "kinetic.api.routes.orchestrate_stream",
            return_value=_simple_stream(),
        ),
    ):
        response = client.post("/api/checkin/stream", json={"message": "Check-in."})

    assert response.status_code == 200
    assert "event: token" in response.text


@pytest.mark.unit
def test_stream_endpoint_body_contains_done_event() -> None:
    """POST /api/checkin/stream response body ends with 'event: done'."""
    with (
        patch(
            "kinetic.api.routes.parse_checkin",
            new_callable=AsyncMock,
            return_value=CheckInPayload(),
        ),
        patch(
            "kinetic.api.routes.orchestrate_stream",
            return_value=_simple_stream(),
        ),
    ):
        response = client.post("/api/checkin/stream", json={"message": "Check-in."})

    assert response.status_code == 200
    assert "event: done" in response.text


@pytest.mark.unit
def test_stream_endpoint_parser_503_on_missing_key() -> None:
    """POST /api/checkin/stream returns 503 if parse_checkin raises OSError."""
    with patch(
        "kinetic.api.routes.parse_checkin",
        new_callable=AsyncMock,
        side_effect=OSError("GEMINI_API_KEY is not set"),
    ):
        response = client.post("/api/checkin/stream", json={"message": "Check-in."})

    assert response.status_code == 503
