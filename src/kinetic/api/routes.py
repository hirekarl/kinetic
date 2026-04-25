from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from kinetic.models.outputs import SystemHealthPayload
from kinetic.orchestrator.lead import orchestrate
from kinetic.parsing.llm_parser import parse_checkin

router = APIRouter(prefix="/api")


class CheckInRequest(BaseModel):
    message: str


@router.post("/checkin", response_model=SystemHealthPayload)
async def checkin(body: CheckInRequest) -> SystemHealthPayload:
    """Accept a natural-language check-in message, parse it, and return system health."""
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    try:
        payload = await parse_checkin(body.message)
    except OSError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Parsing failed: {e}") from e

    return await orchestrate(payload, body.message)
