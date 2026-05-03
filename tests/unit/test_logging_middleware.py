"""Unit tests for StructlogRequestMiddleware."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import structlog
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient
from structlog.testing import capture_logs


def _make_app() -> FastAPI:
    from kinetic.middleware.logging import StructlogRequestMiddleware

    app = FastAPI()
    app.add_middleware(StructlogRequestMiddleware)

    @app.get("/ok")
    async def ok_endpoint() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/context")
    async def context_endpoint() -> dict[str, object]:
        ctx = structlog.contextvars.get_contextvars()
        return dict(ctx)

    return app


# ── request lifecycle events ──────────────────────────────────────────────────


@pytest.mark.unit
def test_middleware_logs_request_start() -> None:
    """Middleware emits a 'request.start' event for every request."""
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    with capture_logs() as cap:
        client.get("/ok")
    events = [e["event"] for e in cap]
    assert "request.start" in events


@pytest.mark.unit
def test_middleware_logs_request_done() -> None:
    """Middleware emits a 'request.done' event after a successful response."""
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    with capture_logs() as cap:
        client.get("/ok")
    done = [e for e in cap if e["event"] == "request.done"]
    assert len(done) == 1


@pytest.mark.unit
def test_middleware_request_done_carries_status_code() -> None:
    """'request.done' event includes the HTTP status code as a field."""
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    with capture_logs() as cap:
        client.get("/ok")
    done = [e for e in cap if e["event"] == "request.done"]
    assert done[0]["status_code"] == 200


@pytest.mark.unit
def test_middleware_request_done_carries_nonnegative_duration() -> None:
    """'request.done' event includes duration_ms >= 0."""
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    with capture_logs() as cap:
        client.get("/ok")
    done = [e for e in cap if e["event"] == "request.done"]
    assert done[0]["duration_ms"] >= 0


# ── context binding ───────────────────────────────────────────────────────────


@pytest.mark.unit
def test_middleware_binds_request_id() -> None:
    """Middleware binds a request_id to structlog context vars for each request."""
    app = _make_app()
    client = TestClient(app)
    resp = client.get("/context")
    assert resp.status_code == 200
    assert "request_id" in resp.json()


@pytest.mark.unit
def test_middleware_binds_path_and_method() -> None:
    """Middleware binds path and method to context vars."""
    app = _make_app()
    client = TestClient(app)
    resp = client.get("/context")
    data = resp.json()
    assert data.get("path") == "/context"
    assert data.get("method") == "GET"


# ── exception handling ────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_middleware_dispatch_exception_emits_error_event() -> None:
    """When call_next raises, middleware logs 'request.error' and re-raises."""
    from kinetic.middleware.logging import StructlogRequestMiddleware

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("127.0.0.1", 8000),
        "root_path": "",
    }
    request = Request(scope)

    async def raising_call_next(req: Request) -> Response:
        raise RuntimeError("boom")

    middleware = StructlogRequestMiddleware(app=MagicMock())

    with capture_logs() as cap, pytest.raises(RuntimeError, match="boom"):
        await middleware.dispatch(request, raising_call_next)

    assert any(e["event"] == "request.error" for e in cap)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_middleware_dispatch_exception_carries_duration() -> None:
    """'request.error' event includes duration_ms >= 0."""
    from kinetic.middleware.logging import StructlogRequestMiddleware

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("127.0.0.1", 8000),
        "root_path": "",
    }
    request = Request(scope)

    async def raising_call_next(req: Request) -> Response:
        raise RuntimeError("boom")

    middleware = StructlogRequestMiddleware(app=MagicMock())

    with capture_logs() as cap, pytest.raises(RuntimeError):
        await middleware.dispatch(request, raising_call_next)

    error_events = [e for e in cap if e["event"] == "request.error"]
    assert len(error_events) == 1
    assert error_events[0]["duration_ms"] >= 0
