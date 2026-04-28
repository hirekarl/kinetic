"""Unit tests for lead.get_db — exercises the real function, not the mock used in test_orchestrator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

import kinetic.orchestrator.lead as lead_module
from kinetic.db.base import DatabaseClient
from kinetic.db.postgres_client import PostgresClient
from kinetic.db.sqlite_client import SqliteClient
from kinetic.orchestrator.lead import _db_clients, get_db


@pytest.fixture(autouse=True)
def reset_db_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear the per-tenant client cache and reset pool before/after each test."""
    _db_clients.clear()
    monkeypatch.setattr(lead_module, "_pg_pool", None)
    yield
    _db_clients.clear()


def test_get_db_default_tenant_uses_sqlite_db_path_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    custom_path = str(tmp_path / "custom.db")
    monkeypatch.setenv("SQLITE_DB_PATH", custom_path)
    db = get_db("default")
    assert "default" in _db_clients
    assert isinstance(db, SqliteClient)
    assert db.db_path == str(Path(custom_path).resolve())


def test_get_db_named_tenant_derives_path_from_tenant_key(tmp_path: Path) -> None:
    db = get_db("demo")
    assert "demo" in _db_clients
    assert isinstance(db, SqliteClient)
    assert db.db_path.endswith("kinetic_demo.db")


def test_get_db_caches_client_on_repeated_calls() -> None:
    first = get_db("personal")
    second = get_db("personal")
    assert first is second


def test_get_db_return_satisfies_database_client_protocol() -> None:
    db = get_db("protocol_test")
    assert isinstance(db, DatabaseClient)


def test_pg_pool_starts_as_none() -> None:
    assert lead_module._pg_pool is None


def test_get_db_returns_sqlite_when_pool_is_none() -> None:
    db = get_db("sqlite_only")
    assert isinstance(db, SqliteClient)


def test_get_db_returns_postgres_client_when_pool_set(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_pool = MagicMock()
    monkeypatch.setattr(lead_module, "_pg_pool", mock_pool)
    db = get_db("my_tenant")
    assert isinstance(db, PostgresClient)
    assert db.tenant == "my_tenant"
    assert db.pool is mock_pool
