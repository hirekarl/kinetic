"""Unit tests for lead.get_db — exercises the real function, not the mock used in test_orchestrator."""

from __future__ import annotations

from pathlib import Path

import pytest

from kinetic.orchestrator.lead import _db_clients, get_db


@pytest.fixture(autouse=True)
def reset_db_cache() -> None:
    """Clear the per-tenant client cache before and after each test."""
    _db_clients.clear()
    yield
    _db_clients.clear()


def test_get_db_default_tenant_uses_sqlite_db_path_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    custom_path = str(tmp_path / "custom.db")
    monkeypatch.setenv("SQLITE_DB_PATH", custom_path)
    db = get_db("default")
    assert "default" in _db_clients
    assert db.db_path == str(Path(custom_path).resolve())


def test_get_db_named_tenant_derives_path_from_tenant_key(tmp_path: Path) -> None:
    db = get_db("demo")
    assert "demo" in _db_clients
    assert db.db_path.endswith("kinetic_demo.db")


def test_get_db_caches_client_on_repeated_calls() -> None:
    first = get_db("personal")
    second = get_db("personal")
    assert first is second
