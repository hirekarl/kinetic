"""Unit tests for application startup behaviour in main.py."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.unit
@pytest.mark.asyncio
async def test_startup_warns_when_api_key_missing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Logger emits a warning at startup when GEMINI_API_KEY is absent."""
    from kinetic.main import app, lifespan

    with (
        patch.dict("os.environ", {}, clear=True),
        caplog.at_level(logging.WARNING, logger="kinetic.main"),
    ):
        async with lifespan(app):
            pass

    assert any(
        "GEMINI_API_KEY" in r.message for r in caplog.records if r.levelno == logging.WARNING
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_startup_no_warning_when_api_key_present(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """No GEMINI_API_KEY warning emitted at startup when the key is set."""
    from kinetic.main import app, lifespan

    with (
        patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-123"}),
        caplog.at_level(logging.WARNING, logger="kinetic.main"),
    ):
        async with lifespan(app):
            pass

    key_warnings = [
        r for r in caplog.records if r.levelno == logging.WARNING and "GEMINI_API_KEY" in r.message
    ]
    assert len(key_warnings) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lifespan_no_database_url_pool_stays_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import kinetic.orchestrator.lead as lead_module
    from kinetic.main import app, lifespan

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(lead_module, "_pg_pool", None)

    async with lifespan(app):
        assert lead_module._pg_pool is None

    assert lead_module._pg_pool is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_lifespan_with_database_url_creates_and_closes_pool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import kinetic.orchestrator.lead as lead_module
    from kinetic.db.postgres_client import PostgresClient
    from kinetic.main import app, lifespan

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/test")
    monkeypatch.setattr(lead_module, "_pg_pool", None)

    mock_pool = MagicMock()
    mock_pool.close = AsyncMock()
    mock_create_pool = AsyncMock(return_value=mock_pool)
    mock_migrate = AsyncMock()

    with (
        patch("asyncpg.create_pool", mock_create_pool),
        patch.object(PostgresClient, "_migrate", mock_migrate),
    ):
        async with lifespan(app):
            assert lead_module._pg_pool is mock_pool

        assert lead_module._pg_pool is None
        mock_pool.close.assert_called_once()
