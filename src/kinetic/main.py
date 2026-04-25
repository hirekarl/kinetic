from __future__ import annotations

from dotenv import load_dotenv  # type: ignore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kinetic.api.routes import router

# Load environment variables from .env at startup
load_dotenv()

app = FastAPI(
    title="Kinetic",
    description="Bio-Operational Triage Engine",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
