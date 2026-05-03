"""Unit tests for kinetic.logging_config — is_production() and setup_logging()."""

from __future__ import annotations

import logging

import pytest


@pytest.fixture(autouse=True)
def reset_logging_state() -> pytest.FixtureRequest:  # type: ignore[override]
    """Restore root logger handlers and _configured flag after each test."""
    import kinetic.logging_config as lc

    original_configured = lc._configured
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    yield
    lc._configured = original_configured
    root_logger.handlers[:] = original_handlers
    root_logger.setLevel(original_level)


# ── is_production() ───────────────────────────────────────────────────────────


@pytest.mark.unit
def test_is_production_default_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returns False when neither RENDER nor LOG_FORMAT env vars are set."""
    from kinetic.logging_config import is_production

    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("LOG_FORMAT", raising=False)
    assert is_production() is False


@pytest.mark.unit
def test_is_production_render_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returns True when RENDER=true."""
    from kinetic.logging_config import is_production

    monkeypatch.setenv("RENDER", "true")
    assert is_production() is True


@pytest.mark.unit
def test_is_production_render_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    """RENDER=True (mixed case) is also accepted."""
    from kinetic.logging_config import is_production

    monkeypatch.setenv("RENDER", "True")
    assert is_production() is True


@pytest.mark.unit
def test_is_production_log_format_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returns True when LOG_FORMAT=json."""
    from kinetic.logging_config import is_production

    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("LOG_FORMAT", "json")
    assert is_production() is True


@pytest.mark.unit
def test_is_production_log_format_other_is_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """LOG_FORMAT=text does not trigger production mode."""
    from kinetic.logging_config import is_production

    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("LOG_FORMAT", "text")
    assert is_production() is False


# ── setup_logging() ───────────────────────────────────────────────────────────


@pytest.mark.unit
def test_setup_logging_installs_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    """setup_logging() installs at least one handler on the root logger."""
    import kinetic.logging_config as lc

    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("LOG_FORMAT", raising=False)

    lc._configured = False
    root = logging.getLogger()
    root.handlers.clear()

    lc.setup_logging()

    assert len(root.handlers) >= 1


@pytest.mark.unit
def test_setup_logging_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Calling setup_logging() twice does not add a second handler."""
    import kinetic.logging_config as lc

    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("LOG_FORMAT", raising=False)

    lc._configured = False
    root = logging.getLogger()
    root.handlers.clear()

    lc.setup_logging()
    count_after_first = len(root.handlers)

    lc.setup_logging()
    assert len(root.handlers) == count_after_first


@pytest.mark.unit
def test_setup_logging_sets_root_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """setup_logging() sets the root logger level to the requested level."""
    import kinetic.logging_config as lc

    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("LOG_FORMAT", raising=False)

    lc._configured = False
    root = logging.getLogger()
    root.handlers.clear()

    lc.setup_logging(log_level="DEBUG")

    assert root.level == logging.DEBUG


@pytest.mark.unit
def test_setup_logging_structlog_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """After setup_logging(), structlog.get_logger() returns a usable logger."""
    import structlog

    import kinetic.logging_config as lc

    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("LOG_FORMAT", raising=False)

    lc._configured = False
    lc.setup_logging()

    log = structlog.get_logger("test.logger")
    # Should not raise
    log.info("test event", key="value")
