"""Tests for the DatabaseClient Protocol — structural compatibility and completeness."""

from __future__ import annotations

from pathlib import Path

import pytest

from kinetic.db.base import DatabaseClient  # fails until base.py exists
from kinetic.db.sqlite_client import SqliteClient

REQUIRED_METHODS = [
    "insert_checkin",
    "get_latest_bio",
    "get_all_tasks",
    "get_all_vibes",
    "get_recent_bio",
    "upsert_contact_pause",
    "get_active_pauses",
    "get_history",
    "get_behavioral_summary",
    "get_behavioral_profiles",
    "upsert_behavioral_profile",
    "complete_task",
    "clear_database",
]


def test_database_client_protocol_is_importable() -> None:
    assert DatabaseClient is not None


@pytest.mark.parametrize("method_name", REQUIRED_METHODS)
def test_database_client_protocol_declares_method(method_name: str) -> None:
    assert hasattr(DatabaseClient, method_name), f"Protocol missing: {method_name}"


def test_sqlite_client_satisfies_database_client_protocol(tmp_path: Path) -> None:
    client = SqliteClient(str(tmp_path / "test.db"))
    assert isinstance(client, DatabaseClient)


def test_sqlite_client_has_all_protocol_methods(tmp_path: Path) -> None:
    client = SqliteClient(str(tmp_path / "test.db"))
    for method_name in REQUIRED_METHODS:
        assert hasattr(client, method_name), f"SqliteClient missing: {method_name}"
