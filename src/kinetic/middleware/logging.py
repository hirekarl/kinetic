from __future__ import annotations

import time
from uuid import uuid4

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

log = structlog.get_logger()


class StructlogRequestMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that binds per-request context and logs lifecycle events.

    Binds request_id, path, and method to structlog context vars at request start
    so every downstream log line in that request automatically carries them.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        structlog.contextvars.clear_contextvars()
        request_id = str(uuid4())
        path = str(request.url.path)
        method = request.method
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=path,
            method=method,
        )
        log.info("request.start", request_id=request_id, path=path, method=method)
        t0 = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - t0) * 1000)
            structlog.contextvars.bind_contextvars(status_code=response.status_code)
            log.info(
                "request.done",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            return response
        except Exception:
            duration_ms = round((time.perf_counter() - t0) * 1000)
            log.exception("request.error", duration_ms=duration_ms)
            raise
