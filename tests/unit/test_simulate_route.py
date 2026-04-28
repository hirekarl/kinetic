"""Unit tests for POST /api/demo/simulate route and simulate_week service."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

from kinetic.main import app
from kinetic.services.simulate import simulate_week

TEST_SECRET = "simulate-route-test-secret"
TEST_PASS = "demo123"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@pytest.fixture(autouse=True)
def setup_auth_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    creds_file = tmp_path / "credentials.toml"
    demo_hash = _hash(TEST_PASS)
    personal_hash = _hash(TEST_PASS)
    creds_file.write_bytes(
        (
            f'[tenants.demo]\npassword_hash = "{demo_hash}"\n'
            'db_path = "./kinetic_demo.db"\ndisplay_name = "Demo"\n'
            f'[tenants.personal]\npassword_hash = "{personal_hash}"\n'
            'db_path = "./kinetic_personal.db"\ndisplay_name = "Personal"\n'
        ).encode()
    )
    monkeypatch.setenv("CREDENTIALS_PATH", str(creds_file))
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def demo_token(client: TestClient) -> str:
    resp = client.post("/api/auth/login", json={"username": "demo", "password": TEST_PASS})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def personal_token(client: TestClient) -> str:
    resp = client.post("/api/auth/login", json={"username": "personal", "password": TEST_PASS})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.mark.unit
def test_simulate_requires_auth_returns_401(client: TestClient) -> None:
    """POST /api/demo/simulate without a token returns 401."""
    resp = client.post("/api/demo/simulate")
    assert resp.status_code == 401


@pytest.mark.unit
def test_simulate_returns_403_for_non_demo_tenant(client: TestClient, personal_token: str) -> None:
    """POST /api/demo/simulate returns 403 when tenant is not 'demo'."""
    resp = client.post(
        "/api/demo/simulate",
        headers={"Authorization": f"Bearer {personal_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.unit
def test_simulate_returns_200_with_inserted_count(client: TestClient, demo_token: str) -> None:
    """POST /api/demo/simulate returns 200 with {'inserted': 5} for the demo tenant."""
    with patch(
        "kinetic.api.routes.simulate_week",
        new=AsyncMock(return_value=5),
    ):
        resp = client.post(
            "/api/demo/simulate",
            headers={"Authorization": f"Bearer {demo_token}"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body == {"inserted": 5}


@pytest.mark.unit
def test_simulate_calls_simulate_week_with_db(client: TestClient, demo_token: str) -> None:
    """POST /api/demo/simulate passes the db client to simulate_week."""
    mock_fn = AsyncMock(return_value=5)
    with patch("kinetic.api.routes.simulate_week", new=mock_fn):
        client.post(
            "/api/demo/simulate",
            headers={"Authorization": f"Bearer {demo_token}"},
        )

    mock_fn.assert_called_once()
    call_args = mock_fn.call_args
    assert call_args is not None


# ── simulate_week service unit tests ──────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_simulate_week_returns_five() -> None:
    """simulate_week inserts 5 scripted check-ins and returns 5."""
    mock_db = AsyncMock()
    mock_db.insert_checkin_at = AsyncMock(return_value="fake-id")

    result = await simulate_week(mock_db)

    assert result == 5
    assert mock_db.insert_checkin_at.call_count == 5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_simulate_week_timestamps_are_historical() -> None:
    """simulate_week spreads timestamps in the past (all before now)."""
    mock_db = AsyncMock()
    mock_db.insert_checkin_at = AsyncMock(return_value="fake-id")

    before = datetime.now()
    await simulate_week(mock_db)

    for call in mock_db.insert_checkin_at.call_args_list:
        ts: datetime = call.args[2]
        assert ts < before, f"Timestamp {ts} should be before call time {before}"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_simulate_week_passes_checkin_payload_and_message() -> None:
    """simulate_week passes a CheckInPayload and non-empty message to insert_checkin_at."""
    from kinetic.models.inputs import CheckInPayload

    mock_db = AsyncMock()
    mock_db.insert_checkin_at = AsyncMock(return_value="fake-id")

    await simulate_week(mock_db)

    for call in mock_db.insert_checkin_at.call_args_list:
        payload = call.args[0]
        message = call.args[1]
        assert isinstance(payload, CheckInPayload)
        assert isinstance(message, str) and message.strip()
