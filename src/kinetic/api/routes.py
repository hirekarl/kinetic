from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from kinetic.auth import get_current_tenant
from kinetic.models.outputs import DigestResponse, SystemHealthPayload
from kinetic.orchestrator.lead import get_current_state, get_db, orchestrate, orchestrate_stream
from kinetic.parsing.llm_parser import parse_checkin
from kinetic.services.digest_generator import generate_digest
from kinetic.services.simulate import simulate_week

router = APIRouter(prefix="/api")


class CheckInRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = Field(default_factory=list)


@router.post("/demo/simulate")
async def demo_simulate(
    tenant: str = Depends(get_current_tenant),
) -> dict[str, int]:
    """Replay 5 scripted check-ins across the past 7 days (demo tenant only)."""
    if tenant != "demo":
        raise HTTPException(status_code=403, detail="Available only for the demo tenant")
    db = get_db(tenant)
    count = await simulate_week(db)
    return {"inserted": count}


@router.get("/digest", response_model=DigestResponse)
async def get_digest(
    force: bool = False,
    tenant: str = Depends(get_current_tenant),
) -> DigestResponse:
    """Return a 14-day prose digest for the authenticated tenant (cached 6 h)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured")
    db = get_db(tenant)
    return await generate_digest(db, api_key, tenant, force=force)


@router.get("/history")
async def fetch_history(tenant: str = Depends(get_current_tenant)) -> dict[str, Any]:
    """Return the current system health and dialogue history for the authenticated tenant."""
    db = get_db(tenant)
    return await get_current_state(db=db)


@router.post("/debug/reset")
async def reset_database(tenant: str = Depends(get_current_tenant)) -> dict[str, str]:
    """Wipe all data for the authenticated tenant (Debug only)."""
    db = get_db(tenant)
    await db.clear_database()
    return {"status": "success", "message": "Database wiped."}


@router.patch("/tasks/{task_name}/complete")
async def complete_task(
    task_name: str,
    tenant: str = Depends(get_current_tenant),
) -> dict[str, str]:
    """Mark a task as completed for the authenticated tenant."""
    db = get_db(tenant)
    try:
        await db.complete_task(task_name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found") from e
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=f"Task '{task_name}' is already completed"
        ) from e
    return {"status": "completed", "task_name": task_name}


@router.post("/checkin/stream")
async def checkin_stream(
    body: CheckInRequest,
    tenant: str = Depends(get_current_tenant),
) -> EventSourceResponse:
    """Stream Operational Liaison response as SSE events."""
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    try:
        payload = await parse_checkin(body.message, body.history)
    except OSError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Parsing failed: {e}") from e

    db = get_db(tenant)
    return EventSourceResponse(orchestrate_stream(payload, body.message, body.history, db=db))


@router.post("/checkin", response_model=SystemHealthPayload)
async def checkin(
    body: CheckInRequest,
    tenant: str = Depends(get_current_tenant),
) -> SystemHealthPayload:
    """Accept a natural-language check-in message, parse it, and return system health."""
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    try:
        payload = await parse_checkin(body.message, body.history)
    except OSError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Parsing failed: {e}") from e

    db = get_db(tenant)
    return await orchestrate(payload, body.message, body.history, db=db)
