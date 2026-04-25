"""Integration tests for the FastAPI routes."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from kinetic.main import app
from kinetic.models.inputs import CheckInPayload

client = TestClient(app)


@pytest.mark.unit
def test_health_check() -> None:
    """GET /health returns 200 ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.unit
def test_checkin_empty_message_returns_400() -> None:
    """POST /api/checkin with empty message returns 400."""
    response = client.post("/api/checkin", json={"message": ""})
    assert response.status_code == 400
    assert "message must not be empty" in response.json()["detail"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_checkin_success_path() -> None:
    """POST /api/checkin calls parser and orchestrator correctly."""
    mock_payload = CheckInPayload(bio={"sleep_hours": 8.0})

    with patch(
        "kinetic.api.routes.parse_checkin", new_callable=AsyncMock, return_value=mock_payload
    ):
        # We don't need to mock orchestrate because it will run with the mock_payload
        response = client.post("/api/checkin", json={"message": "Slept 8 hours."})

    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] == "green"
    assert data["bio"]["status"] == "green"
    assert data["bio"]["burnout_score"] == 0.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_checkin_parser_failure_returns_503() -> None:
    """If parse_checkin raises OSError (missing key), return 503."""
    with patch(
        "kinetic.api.routes.parse_checkin",
        new_callable=AsyncMock,
        side_effect=OSError("GEMINI_API_KEY is not set"),
    ):
        response = client.post("/api/checkin", json={"message": "Slept 8 hours."})

    assert response.status_code == 503
    assert "GEMINI_API_KEY is not set" in response.json()["detail"]
