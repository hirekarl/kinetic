from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kinetic.api.auth import router as auth_router
from kinetic.api.routes import router
from kinetic.orchestrator import lead

load_dotenv()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if not os.environ.get("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY is not set — LLM features will return 503")
    if not os.environ.get("SECRET_KEY"):
        logger.warning("SECRET_KEY not set — JWT signing will fail at runtime")
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        import asyncpg

        from kinetic.db.postgres_client import PostgresClient

        lead._pg_pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)
        await PostgresClient(lead._pg_pool, "default")._migrate()
        logger.info("PostgreSQL pool created and schema migrated")
    else:
        logger.info("DATABASE_URL not set — using SQLite")
    yield
    if lead._pg_pool is not None:
        await lead._pg_pool.close()
        lead._pg_pool = None


app = FastAPI(
    title="Kinetic",
    description="Bio-Operational Triage Engine",
    version="0.1.0",
    lifespan=lifespan,
)

_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if _frontend_url := os.environ.get("FRONTEND_URL"):
    _origins.append(_frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
