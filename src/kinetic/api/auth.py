from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from kinetic.auth import (
    CurrentUser,
    create_access_token,
    get_current_user,
    load_credentials,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

log = structlog.get_logger()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Verify credentials and return a signed JWT."""
    try:
        creds = load_credentials()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Credentials store unavailable",
        ) from exc

    tenant_cfg = creds.get(body.username)
    if tenant_cfg is None or not verify_password(body.password, tenant_cfg.password_hash):
        log.warning("auth.login.failure", username=body.username, reason="invalid_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(body.username, body.username)
    log.info("auth.login.success", username=body.username, tenant=body.username)
    return TokenResponse(access_token=token, tenant=body.username)


@router.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)) -> dict[str, str]:
    """Return the authenticated user's profile, including tenant display name."""
    try:
        creds = load_credentials()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Credentials store unavailable",
        ) from exc

    tenant_cfg = creds.get(user.username)
    if tenant_cfg is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant not found",
        )
    return {
        "username": user.username,
        "tenant": user.tenant,
        "display_name": tenant_cfg.display_name,
    }


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Stateless logout — client drops the token. Returns 200 for UX completeness."""
    return {"status": "ok"}
