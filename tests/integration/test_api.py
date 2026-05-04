"""Integration tests for the FastAPI routes."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from kinetic.auth import get_current_tenant
from kinetic.main import app
from kinetic.models.inputs import BioInput, CheckInPayload
from kinetic.models.outputs import BioStatus, SystemHealthPayload

client = TestClient(app)


@pytest.fixture(autouse=True)
def bypass_auth() -> Generator[None, None, None]:
    """Override get_current_tenant for all tests in this module — auth is tested separately."""
    app.dependency_overrides[get_current_tenant] = lambda: "test"
    yield
    app.dependency_overrides.pop(get_current_tenant, None)


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
    """POST /api/checkin wires parser → orchestrator and returns a valid SystemHealthPayload."""
    mock_payload = CheckInPayload(bio=BioInput(sleep_hours=8.0))
    mock_health = SystemHealthPayload(
        overall_status="green",
        bio=BioStatus(status="green", burnout_score=20.0, forecast="Looking good."),
        triage_items=[],
        behavioral_profiles=[],
    )

    with (
        patch(
            "kinetic.api.routes.parse_checkin", new_callable=AsyncMock, return_value=mock_payload
        ),
        patch("kinetic.api.routes.orchestrate", new_callable=AsyncMock, return_value=mock_health),
    ):
        response = client.post("/api/checkin", json={"message": "Slept 8 hours."})

    assert response.status_code == 200
    data = response.json()
    assert data["overall_status"] in ("green", "yellow", "red")
    assert "bio" in data
    assert "triage_items" in data
    assert "behavioral_profiles" in data  # new Behavioral Memory field


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


# ── Task completion endpoint ──────────────────────────────────────────────────


@pytest.mark.unit
def test_complete_task_returns_200_for_known_task() -> None:
    """PATCH /api/tasks/{task_name}/complete returns 200 when task exists."""
    with patch("kinetic.api.routes.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.complete_task = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db

        response = client.patch("/api/tasks/laundry/complete")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["task_name"] == "laundry"


@pytest.mark.unit
def test_complete_task_returns_404_for_unknown_task() -> None:
    """PATCH /api/tasks/{task_name}/complete returns 404 when task is not found."""
    with patch("kinetic.api.routes.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.complete_task = AsyncMock(side_effect=KeyError("nonexistent"))
        mock_get_db.return_value = mock_db

        response = client.patch("/api/tasks/nonexistent/complete")

    assert response.status_code == 404


@pytest.mark.unit
def test_complete_task_returns_409_for_already_completed() -> None:
    """PATCH /api/tasks/{task_name}/complete returns 409 when already completed."""
    with patch("kinetic.api.routes.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.complete_task = AsyncMock(side_effect=ValueError("already completed"))
        mock_get_db.return_value = mock_db

        response = client.patch("/api/tasks/laundry/complete")

    assert response.status_code == 409


# ── PATCH /api/tasks/{task_name}/subtasks ─────────────────────────────────────


@pytest.mark.unit
def test_patch_subtask_returns_200_on_success() -> None:
    """PATCH /api/tasks/{task_name}/subtasks returns 200 with subtask_completed status."""
    with patch("kinetic.api.routes.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.complete_subtask = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db

        response = client.patch("/api/tasks/laundry/subtasks", json={"subtask": "sort"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "subtask_completed"
    assert body["task_name"] == "laundry"
    assert body["subtask"] == "sort"


@pytest.mark.unit
def test_patch_subtask_returns_404_for_unknown_task() -> None:
    """PATCH /api/tasks/{task_name}/subtasks returns 404 when task is not found."""
    with patch("kinetic.api.routes.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.complete_subtask = AsyncMock(side_effect=KeyError("ghost"))
        mock_get_db.return_value = mock_db

        response = client.patch("/api/tasks/ghost/subtasks", json={"subtask": "step1"})

    assert response.status_code == 404


@pytest.mark.unit
def test_patch_subtask_returns_422_for_unknown_subtask() -> None:
    """PATCH /api/tasks/{task_name}/subtasks returns 422 when subtask not in task."""
    with patch("kinetic.api.routes.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.complete_subtask = AsyncMock(side_effect=ValueError("iron"))
        mock_get_db.return_value = mock_db

        response = client.patch("/api/tasks/laundry/subtasks", json={"subtask": "iron"})

    assert response.status_code == 422


@pytest.mark.unit
def test_patch_subtask_requires_auth() -> None:
    """PATCH /api/tasks/{task_name}/subtasks returns 401 without JWT (auth bypass removed)."""
    app.dependency_overrides.pop(get_current_tenant, None)
    try:
        response = client.patch("/api/tasks/laundry/subtasks", json={"subtask": "sort"})
        assert response.status_code == 401
    finally:
        app.dependency_overrides[get_current_tenant] = lambda: "test"


@pytest.mark.unit
def test_patch_subtask_requires_subtask_body() -> None:
    """PATCH /api/tasks/{task_name}/subtasks returns 422 when body is missing subtask field."""
    response = client.patch("/api/tasks/laundry/subtasks", json={})
    assert response.status_code == 422


# ── POST /api/debug/reset ─────────────────────────────────────────────────────


@pytest.mark.unit
def test_reset_database_returns_200_success() -> None:
    """POST /api/debug/reset clears the DB and returns {status: success}."""
    with patch("kinetic.api.routes.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_db.clear_database = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db

        response = client.post("/api/debug/reset")

    assert response.status_code == 200
    assert response.json()["status"] == "success"


# ── Generic exception handler in checkin routes ───────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_checkin_generic_parse_exception_returns_500() -> None:
    """If parse_checkin raises a non-OSError exception, /api/checkin returns 500."""
    with patch(
        "kinetic.api.routes.parse_checkin",
        new_callable=AsyncMock,
        side_effect=RuntimeError("unexpected parsing failure"),
    ):
        response = client.post("/api/checkin", json={"message": "Slept 8 hours."})

    assert response.status_code == 500
    assert "LLM Parsing failed" in response.json()["detail"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_checkin_stream_generic_parse_exception_returns_500() -> None:
    """If parse_checkin raises a non-OSError exception, /api/checkin/stream returns 500."""
    with patch(
        "kinetic.api.routes.parse_checkin",
        new_callable=AsyncMock,
        side_effect=RuntimeError("stream parse failure"),
    ):
        response = client.post("/api/checkin/stream", json={"message": "Slept 8 hours."})

    assert response.status_code == 500
    assert "LLM Parsing failed" in response.json()["detail"]
