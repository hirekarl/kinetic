"""Unit tests for GET /api/digest route — shape, auth, force param, 503 guard."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import bcrypt
import pytest
from fastapi.testclient import TestClient

from kinetic.main import app
from kinetic.models.outputs import DigestResponse

TEST_SECRET = "digest-route-test-secret"
TEST_PASS = "demo123"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@pytest.fixture(autouse=True)
def setup_auth_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    creds_file = tmp_path / "credentials.toml"
    demo_hash = _hash(TEST_PASS)
    creds_file.write_bytes(
        (
            f'[tenants.demo]\npassword_hash = "{demo_hash}"\n'
            'db_path = "./kinetic_demo.db"\ndisplay_name = "Demo"\n'
        ).encode()
    )
    monkeypatch.setenv("CREDENTIALS_PATH", str(creds_file))
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def demo_token(client: TestClient) -> str:
    resp = client.post("/api/auth/login", json={"username": "demo", "password": TEST_PASS})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


_FAKE_DIGEST = DigestResponse(
    summary="You slept 6.5 hours on average last week.",
    generated_at=datetime(2026, 4, 28, 10, 0, 0),
)


@pytest.mark.unit
def test_digest_returns_200_with_digest_shape(client: TestClient, demo_token: str) -> None:
    """GET /api/digest returns 200 with summary and generated_at fields."""
    with patch(
        "kinetic.api.routes.generate_digest",
        new=AsyncMock(return_value=_FAKE_DIGEST),
    ):
        resp = client.get(
            "/api/digest",
            headers={"Authorization": f"Bearer {demo_token}"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "summary" in body
    assert "generated_at" in body
    assert body["summary"] == _FAKE_DIGEST.summary


@pytest.mark.unit
def test_digest_force_false_by_default(client: TestClient, demo_token: str) -> None:
    """GET /api/digest without ?force calls generate_digest with force=False."""
    mock_fn = AsyncMock(return_value=_FAKE_DIGEST)
    with patch("kinetic.api.routes.generate_digest", new=mock_fn):
        client.get(
            "/api/digest",
            headers={"Authorization": f"Bearer {demo_token}"},
        )

    _, kwargs = mock_fn.call_args
    assert kwargs.get("force") is False


@pytest.mark.unit
def test_digest_force_true_forwarded(client: TestClient, demo_token: str) -> None:
    """GET /api/digest?force=true passes force=True to generate_digest."""
    mock_fn = AsyncMock(return_value=_FAKE_DIGEST)
    with patch("kinetic.api.routes.generate_digest", new=mock_fn):
        client.get(
            "/api/digest?force=true",
            headers={"Authorization": f"Bearer {demo_token}"},
        )

    _, kwargs = mock_fn.call_args
    assert kwargs.get("force") is True


@pytest.mark.unit
def test_digest_requires_auth_returns_401(client: TestClient) -> None:
    """GET /api/digest without a token returns 401."""
    resp = client.get("/api/digest")
    assert resp.status_code == 401


@pytest.mark.unit
def test_digest_503_when_gemini_api_key_missing(
    client: TestClient,
    demo_token: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /api/digest returns 503 when GEMINI_API_KEY is not set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    resp = client.get(
        "/api/digest",
        headers={"Authorization": f"Bearer {demo_token}"},
    )
    assert resp.status_code == 503
