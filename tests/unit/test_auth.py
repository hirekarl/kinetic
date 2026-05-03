"""Unit tests for kinetic.auth — password hashing, JWT encode/decode, credential loading."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import bcrypt
import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from kinetic.auth import (
    CurrentUser,
    TenantConfig,
    create_access_token,
    decode_access_token,
    get_current_tenant,
    get_current_user,
    load_credentials,
    verify_password,
)

TEST_SECRET = "test-secret-key-for-unit-tests-only"


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@pytest.fixture(autouse=True)
def set_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SECRET_KEY", TEST_SECRET)


# ── verify_password ────────────────────────────────────────────────────────────


def test_verify_password_correct() -> None:
    hashed = _hash("correct_password")
    assert verify_password("correct_password", hashed) is True


def test_verify_password_wrong() -> None:
    hashed = _hash("correct_password")
    assert verify_password("wrong_password", hashed) is False


# ── create_access_token + decode_access_token ──────────────────────────────────


def test_token_round_trip_carries_sub_and_tenant() -> None:
    token = create_access_token("demo_user", "demo")
    payload = decode_access_token(token)
    assert payload["sub"] == "demo_user"
    assert payload["tenant"] == "demo"


def test_decode_expired_token_raises_401() -> None:
    expired_payload = {
        "sub": "demo_user",
        "tenant": "demo",
        "exp": datetime.now(tz=UTC) - timedelta(hours=1),
    }
    expired_token = jwt.encode(expired_payload, TEST_SECRET, algorithm="HS256")
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(expired_token)
    assert exc_info.value.status_code == 401


def test_decode_tampered_token_raises_401() -> None:
    token = create_access_token("demo_user", "demo")
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token + "tampered")
    assert exc_info.value.status_code == 401


def test_decode_token_wrong_secret_raises_401(monkeypatch: pytest.MonkeyPatch) -> None:
    token = create_access_token("demo_user", "demo")
    monkeypatch.setenv("SECRET_KEY", "different-secret")
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token)
    assert exc_info.value.status_code == 401


# ── load_credentials ───────────────────────────────────────────────────────────


def test_load_credentials_returns_tenant_configs(tmp_path: Path) -> None:
    creds_file = tmp_path / "credentials.toml"
    creds_file.write_bytes(
        b'[tenants.demo]\npassword_hash = "$2b$12$HASH"\n'
        b'db_path = "./kinetic_demo.db"\ndisplay_name = "Demo"\n\n'
        b'[tenants.personal]\npassword_hash = "$2b$12$HASH2"\n'
        b'db_path = "./kinetic_personal.db"\ndisplay_name = "Karl"\n'
    )
    result = load_credentials(creds_file)
    assert set(result.keys()) == {"demo", "personal"}
    assert isinstance(result["demo"], TenantConfig)
    assert result["demo"].display_name == "Demo"
    assert result["personal"].display_name == "Karl"


def test_load_credentials_missing_file_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_credentials("/nonexistent/path/credentials.toml")


# ── get_current_user dependency ────────────────────────────────────────────────


async def test_get_current_user_valid_token() -> None:
    token = create_access_token("demo_user", "demo")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = await get_current_user(creds)
    assert user.username == "demo_user"
    assert user.tenant == "demo"


async def test_get_current_user_invalid_token_raises_401() -> None:
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not.a.real.token")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(creds)
    assert exc_info.value.status_code == 401


async def test_get_current_user_no_credentials_raises_401() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None)
    assert exc_info.value.status_code == 401


# ── get_current_tenant dependency ─────────────────────────────────────────────


async def test_get_current_tenant_returns_tenant_string() -> None:
    user = CurrentUser(username="demo_user", tenant="demo")
    tenant = await get_current_tenant(user)
    assert tenant == "demo"


def test_create_access_token_raises_when_secret_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """create_access_token raises RuntimeError when SECRET_KEY env var is empty."""
    monkeypatch.delenv("SECRET_KEY")
    with pytest.raises(RuntimeError, match="SECRET_KEY is not set"):
        create_access_token("demo_user", "demo")


async def test_get_current_user_missing_sub_in_payload_raises_401() -> None:
    """Token missing 'sub' claim → get_current_user raises 401."""
    from datetime import UTC, datetime, timedelta

    import jwt as _jwt

    no_sub_payload = {
        "tenant": "demo",
        "exp": datetime.now(tz=UTC) + timedelta(hours=1),
    }
    token = _jwt.encode(no_sub_payload, TEST_SECRET, algorithm="HS256")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(creds)
    assert exc_info.value.status_code == 401
