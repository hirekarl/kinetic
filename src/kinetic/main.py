from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kinetic.api.auth import router as auth_router
from kinetic.api.routes import router
from kinetic.logging_config import setup_logging
from kinetic.middleware.logging import StructlogRequestMiddleware
from kinetic.orchestrator import lead

load_dotenv()
setup_logging()

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown.

    On startup, emits warnings for missing required environment variables and,
    when DATABASE_URL is set, creates an asyncpg connection pool and runs the
    idempotent DDL migration.  Falls back to SQLite when DATABASE_URL is absent.
    On shutdown, closes the pool if one was created.

    Args:
        app: The FastAPI application instance (unused directly; required by protocol).
    """
    if not os.environ.get("GEMINI_API_KEY"):
        log.warning("GEMINI_API_KEY is not set — LLM features will return 503")
    if not os.environ.get("SECRET_KEY"):
        log.warning("SECRET_KEY not set — JWT signing will fail at runtime")
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        import asyncpg

        from kinetic.db.postgres_client import PostgresClient

        lead._pg_pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)
        await PostgresClient(lead._pg_pool, "default")._migrate()
        log.info("db.pool.created", backend="postgresql")
    else:
        log.info("db.sqlite.fallback")
    yield
    if lead._pg_pool is not None:
        await lead._pg_pool.close()
        lead._pg_pool = None
        log.info("db.pool.closed")


app = FastAPI(
    title="Kinetic",
    description="Bio-Operational Triage Engine",
    version="0.1.0",
    lifespan=lifespan,
)

_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if _frontend_url := os.environ.get("FRONTEND_URL"):
    _origins.append(_frontend_url.rstrip("/"))

app.add_middleware(StructlogRequestMiddleware)
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
