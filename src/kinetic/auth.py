from __future__ import annotations

import os
import tomllib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import bcrypt
import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

log = structlog.get_logger()

_bearer = HTTPBearer(auto_error=False)

_JWT_ALGORITHM = "HS256"
_JWT_EXPIRY_HOURS = 8


class TenantConfig(BaseModel):
    password_hash: str
    db_path: str
    display_name: str


class CurrentUser(BaseModel):
    username: str
    tenant: str


def load_credentials(path: str | Path | None = None) -> dict[str, TenantConfig]:
    """Load tenant configs from TOML. Path defaults to CREDENTIALS_PATH env var or credentials.toml."""
    if path is None:
        path = os.environ.get("CREDENTIALS_PATH", "credentials.toml")
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Credentials file not found: {resolved}")
    with resolved.open("rb") as f:
        data = tomllib.load(f)
    return {username: TenantConfig(**cfg) for username, cfg in data.get("tenants", {}).items()}


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(username: str, tenant: str) -> str:
    """Sign a JWT with SECRET_KEY (HS256, 8 h expiry). Raises RuntimeError if key unset."""
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        raise RuntimeError("SECRET_KEY is not set")
    payload: dict[str, Any] = {
        "sub": username,
        "tenant": tenant,
        "exp": datetime.now(tz=UTC) + timedelta(hours=_JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, secret, algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises HTTPException 401 on any failure."""
    secret = os.environ.get("SECRET_KEY", "")
    try:
        result: dict[str, Any] = jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
        return result
    except jwt.ExpiredSignatureError as exc:
        log.warning("auth.token.expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.PyJWTError as exc:
        log.warning("auth.token.invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    """FastAPI dependency. Returns CurrentUser from Bearer token. Raises 401 if absent/invalid."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    username: str | None = payload.get("sub")
    tenant: str | None = payload.get("tenant")
    if not username or not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = CurrentUser(username=username, tenant=tenant)
    structlog.contextvars.bind_contextvars(tenant=user.tenant)
    return user


async def get_current_tenant(
    user: CurrentUser = Depends(get_current_user),
) -> str:
    """FastAPI dependency shorthand that returns only the tenant string."""
    return user.tenant
