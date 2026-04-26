"""Unit tests for application startup behaviour in main.py."""

from __future__ import annotations

import logging
from unittest.mock import patch

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
