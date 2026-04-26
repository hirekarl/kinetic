from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from kinetic.models.outputs import SystemHealthPayload
from kinetic.orchestrator.lead import get_current_state, get_db, orchestrate
from kinetic.parsing.llm_parser import parse_checkin

router = APIRouter(prefix="/api")


class CheckInRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = Field(default_factory=list)


@router.get("/history")
async def fetch_history() -> dict[str, Any]:
    """Return the current system health and dialogue history."""
    return await get_current_state()


@router.post("/debug/reset")
async def reset_database() -> dict[str, str]:
    """Wipe all data from the graph database (Debug only)."""
    db = get_db()
    await db.clear_database()
    return {"status": "success", "message": "Database wiped."}


@router.patch("/tasks/{task_name}/complete")
async def complete_task(task_name: str) -> dict[str, str]:
    """Mark a task as completed."""
    db = get_db()
    try:
        await db.complete_task(task_name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found") from e
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=f"Task '{task_name}' is already completed"
        ) from e
    return {"status": "completed", "task_name": task_name}


@router.post("/checkin", response_model=SystemHealthPayload)
async def checkin(body: CheckInRequest) -> SystemHealthPayload:
    """Accept a natural-language check-in message, parse it, and return system health."""
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    try:
        payload = await parse_checkin(body.message, body.history)
    except OSError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Parsing failed: {e}") from e

    return await orchestrate(payload, body.message, body.history)
