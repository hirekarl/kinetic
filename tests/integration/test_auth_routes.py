"""Integration tests for auth endpoints and protected route gating."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

from kinetic.main import app
from kinetic.models.outputs import SystemHealthPayload

TEST_SECRET = "integration-test-secret-key"
TEST_DEMO_PASS = "demo123"
TEST_PERSONAL_PASS = "personal123"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@pytest.fixture(autouse=True)
def setup_auth_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set test SECRET_KEY and point CREDENTIALS_PATH at a temp credentials file."""
    creds_file = tmp_path / "credentials.toml"
    demo_hash = _hash(TEST_DEMO_PASS)
    personal_hash = _hash(TEST_PERSONAL_PASS)
    creds_file.write_bytes(
        (
            f'[tenants.demo]\npassword_hash = "{demo_hash}"\n'
            f'db_path = "./kinetic_demo.db"\ndisplay_name = "Demo"\n\n'
            f'[tenants.personal]\npassword_hash = "{personal_hash}"\n'
            f'db_path = "./kinetic_personal.db"\ndisplay_name = "Karl"\n'
        ).encode()
    )
    monkeypatch.setenv("CREDENTIALS_PATH", str(creds_file))
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def demo_token(client: TestClient) -> str:
    resp = client.post("/api/auth/login", json={"username": "demo", "password": TEST_DEMO_PASS})
    assert resp.status_code == 200, resp.text
    return str(resp.json()["access_token"])


@pytest.fixture
def demo_headers(demo_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {demo_token}"}


# ── POST /api/auth/login ───────────────────────────────────────────────────────


def test_login_returns_token_for_valid_demo_credentials(client: TestClient) -> None:
    resp = client.post("/api/auth/login", json={"username": "demo", "password": TEST_DEMO_PASS})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["tenant"] == "demo"


def test_login_returns_401_for_wrong_password(client: TestClient) -> None:
    resp = client.post("/api/auth/login", json={"username": "demo", "password": "wrong"})
    assert resp.status_code == 401


def test_login_returns_401_for_unknown_user(client: TestClient) -> None:
    resp = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert resp.status_code == 401


# ── GET /api/auth/me ──────────────────────────────────────────────────────────


def test_me_returns_user_info_with_valid_token(
    client: TestClient, demo_headers: dict[str, str]
) -> None:
    resp = client.get("/api/auth/me", headers=demo_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "demo"
    assert data["tenant"] == "demo"
    assert data["display_name"] == "Demo"


def test_me_returns_401_with_no_token(client: TestClient) -> None:
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_401_with_invalid_token(client: TestClient) -> None:
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


# ── POST /api/auth/logout ─────────────────────────────────────────────────────


def test_logout_returns_ok(client: TestClient, demo_headers: dict[str, str]) -> None:
    resp = client.post("/api/auth/logout", headers=demo_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Protected routes — no token ───────────────────────────────────────────────


def test_checkin_without_token_returns_401(client: TestClient) -> None:
    resp = client.post("/api/checkin", json={"message": "hello"})
    assert resp.status_code == 401


def test_history_without_token_returns_401(client: TestClient) -> None:
    resp = client.get("/api/history")
    assert resp.status_code == 401


# ── Protected routes — with valid token ───────────────────────────────────────


def test_checkin_with_valid_token_succeeds(
    client: TestClient, demo_headers: dict[str, str]
) -> None:
    mock_payload = MagicMock()
    mock_health = SystemHealthPayload(
        overall_status="green", triage_items=[], behavioral_profiles=[]
    )
    with (
        patch(
            "kinetic.api.routes.parse_checkin", new_callable=AsyncMock, return_value=mock_payload
        ),
        patch("kinetic.api.routes.orchestrate", new_callable=AsyncMock, return_value=mock_health),
    ):
        resp = client.post(
            "/api/checkin",
            json={"message": "Slept 8 hours."},
            headers=demo_headers,
        )
    assert resp.status_code == 200


def test_history_with_valid_token_succeeds(
    client: TestClient, demo_headers: dict[str, str]
) -> None:
    with patch(
        "kinetic.api.routes.get_current_state",
        new_callable=AsyncMock,
        return_value={"health": None, "messages": []},
    ):
        resp = client.get("/api/history", headers=demo_headers)
    assert resp.status_code == 200


# ── Credentials store unavailable (FileNotFoundError) ─────────────────────────


def test_login_returns_503_when_credentials_store_unavailable(client: TestClient) -> None:
    """POST /api/auth/login returns 503 when credentials file cannot be loaded."""
    with patch("kinetic.api.auth.load_credentials", side_effect=FileNotFoundError("missing")):
        resp = client.post("/api/auth/login", json={"username": "demo", "password": "any"})
    assert resp.status_code == 503
    assert "unavailable" in resp.json()["detail"].lower()


def test_me_returns_503_when_credentials_store_unavailable(
    client: TestClient, demo_headers: dict[str, str]
) -> None:
    """GET /api/auth/me returns 503 when credentials file cannot be loaded."""
    with patch("kinetic.api.auth.load_credentials", side_effect=FileNotFoundError("missing")):
        resp = client.get("/api/auth/me", headers=demo_headers)
    assert resp.status_code == 503
    assert "unavailable" in resp.json()["detail"].lower()


def test_me_returns_401_when_tenant_not_in_credentials(client: TestClient) -> None:
    """GET /api/auth/me returns 401 when token user is absent from credentials store."""
    from datetime import UTC, datetime, timedelta

    import jwt as _jwt

    ghost_token = _jwt.encode(
        {
            "sub": "ghost_user",
            "tenant": "ghost",
            "exp": datetime.now(tz=UTC) + timedelta(hours=1),
        },
        TEST_SECRET,
        algorithm="HS256",
    )
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {ghost_token}"})
    assert resp.status_code == 401
