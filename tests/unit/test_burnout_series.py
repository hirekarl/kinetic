"""Unit tests for get_burnout_series() — SqliteClient + Protocol + behavioral_summary wiring."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from kinetic.db.sqlite_client import SqliteClient
from kinetic.models.inputs import BioInput, CheckInPayload

# ── helpers ───────────────────────────────────────────────────────────────────


def _bio_payload(
    sleep_hours: float | None = None,
    nutrition_quality: int | None = None,
    energy_level: int | None = None,
) -> CheckInPayload:
    return CheckInPayload(
        bio=BioInput(
            sleep_hours=sleep_hours,
            nutrition_quality=nutrition_quality,
            energy_level=energy_level,
        )
    )


# ── SqliteClient.get_burnout_series ───────────────────────────────────────────


@pytest.mark.unit
async def test_get_burnout_series_empty_db(tmp_path: Path) -> None:
    """Empty database returns an empty list."""
    client = SqliteClient(str(tmp_path / "test.db"))
    result = await client.get_burnout_series()
    assert result == []


@pytest.mark.unit
async def test_get_burnout_series_single_entry_returns_one_score(tmp_path: Path) -> None:
    """One bio check-in produces a list with exactly one float in [0, 100]."""
    client = SqliteClient(str(tmp_path / "test.db"))
    await client.insert_checkin(
        _bio_payload(sleep_hours=6.0, nutrition_quality=7, energy_level=6), "msg"
    )
    result = await client.get_burnout_series()
    assert len(result) == 1
    assert 0.0 <= result[0] <= 100.0


@pytest.mark.unit
async def test_get_burnout_series_score_matches_bio_archivist_formula(tmp_path: Path) -> None:
    """Score for (sleep=6, nutrition=7, energy=6) matches the BioArchivist weighted formula."""
    # sleep_component(6)   = min(100, (8-6)*25) = 50.0
    # nutrition_component(7) = (10-7)/9*100     = 33.33...
    # energy_component(6)  = (10-6)/9*100       = 44.44...
    # weighted_sum = 0.4*50 + 0.3*33.33 + 0.3*44.44 = 43.33...
    client = SqliteClient(str(tmp_path / "test.db"))
    await client.insert_checkin(
        _bio_payload(sleep_hours=6.0, nutrition_quality=7, energy_level=6), "msg"
    )
    result = await client.get_burnout_series()
    assert len(result) == 1
    assert result[0] == pytest.approx(43.33, abs=0.1)


@pytest.mark.unit
async def test_get_burnout_series_multiple_entries_ordered_oldest_first(tmp_path: Path) -> None:
    """Series is ordered oldest→newest: high-sleep (low burnout) first, low-sleep (high burnout) last."""
    client = SqliteClient(str(tmp_path / "test.db"))
    # Good sleep first → low burnout
    await client.insert_checkin(
        _bio_payload(sleep_hours=8.0, nutrition_quality=9, energy_level=9), "good"
    )
    await asyncio.sleep(0.01)
    # Bad sleep second → high burnout
    await client.insert_checkin(
        _bio_payload(sleep_hours=4.0, nutrition_quality=3, energy_level=3), "bad"
    )

    result = await client.get_burnout_series()

    assert len(result) == 2
    assert result[0] < result[1], "Oldest (good) entry should have lower burnout than newest (bad)"


@pytest.mark.unit
async def test_get_burnout_series_days_filter_excludes_old_entries(tmp_path: Path) -> None:
    """Entries outside the `days` window are not included in the series."""
    client = SqliteClient(str(tmp_path / "test.db"))
    # Insert one entry, then ask for 0 days (empty window)
    await client.insert_checkin(
        _bio_payload(sleep_hours=7.0, nutrition_quality=8, energy_level=7), "msg"
    )
    result = await client.get_burnout_series(days=0)
    assert result == []


@pytest.mark.unit
async def test_get_burnout_series_partial_data_only_sleep(tmp_path: Path) -> None:
    """Rows with only sleep_hours produce a valid score (other components skipped)."""
    client = SqliteClient(str(tmp_path / "test.db"))
    await client.insert_checkin(_bio_payload(sleep_hours=5.0), "msg")
    result = await client.get_burnout_series()
    assert len(result) == 1
    # sleep_component(5) = min(100, (8-5)*25) = 75; only sleep weight → score = 75
    assert result[0] == pytest.approx(75.0, abs=0.01)


@pytest.mark.unit
async def test_get_burnout_series_all_none_fields_returns_zero(tmp_path: Path) -> None:
    """A bio row with all None fields (no data) produces a score of 0.0."""
    client = SqliteClient(str(tmp_path / "test.db"))
    await client.insert_checkin(_bio_payload(), "msg")
    result = await client.get_burnout_series()
    # No fields → total_weight=0 → score=0.0
    assert len(result) == 1
    assert result[0] == 0.0


@pytest.mark.unit
async def test_get_burnout_series_perfect_health_low_score(tmp_path: Path) -> None:
    """Perfect stats (8h sleep, nutrition=10, energy=10) → burnout score near 0."""
    client = SqliteClient(str(tmp_path / "test.db"))
    await client.insert_checkin(
        _bio_payload(sleep_hours=8.0, nutrition_quality=10, energy_level=10), "msg"
    )
    result = await client.get_burnout_series()
    assert len(result) == 1
    assert result[0] == pytest.approx(0.0, abs=0.01)


# ── get_behavioral_summary wiring ─────────────────────────────────────────────


@pytest.mark.unit
async def test_behavioral_summary_bio_trend_includes_burnout_series(tmp_path: Path) -> None:
    """get_behavioral_summary() populates bio_trend.burnout_series when bio data exists."""
    client = SqliteClient(str(tmp_path / "test.db"))
    await client.insert_checkin(
        _bio_payload(sleep_hours=6.5, nutrition_quality=7, energy_level=6), "msg"
    )
    summary = await client.get_behavioral_summary()
    assert summary.bio_trend is not None
    assert len(summary.bio_trend.burnout_series) == 1
    assert 0.0 <= summary.bio_trend.burnout_series[0] <= 100.0


@pytest.mark.unit
async def test_behavioral_summary_burnout_series_empty_when_no_bio(tmp_path: Path) -> None:
    """When no bio data exists, bio_trend is None and there is no burnout_series to populate."""
    client = SqliteClient(str(tmp_path / "test.db"))
    # Insert a non-bio check-in so days_analyzed > 0 doesn't short-circuit
    from kinetic.models.inputs import LogisticsInput, LogisticsTask

    logistics_payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="errand", days_overdue=1, priority="low")]
        )
    )
    await client.insert_checkin(logistics_payload, "msg")
    summary = await client.get_behavioral_summary()
    assert summary.bio_trend is None


@pytest.mark.unit
async def test_behavioral_summary_burnout_series_matches_standalone_method(tmp_path: Path) -> None:
    """burnout_series in bio_trend matches the standalone get_burnout_series() output."""
    client = SqliteClient(str(tmp_path / "test.db"))
    await client.insert_checkin(
        _bio_payload(sleep_hours=7.0, nutrition_quality=8, energy_level=7), "msg"
    )

    standalone = await client.get_burnout_series()
    summary = await client.get_behavioral_summary()

    assert summary.bio_trend is not None
    assert summary.bio_trend.burnout_series == standalone


# ── PostgresClient (mocked pool) ──────────────────────────────────────────────


@pytest.mark.unit
async def test_postgres_get_burnout_series_empty_result(tmp_path: Path) -> None:
    """PostgresClient.get_burnout_series() returns [] when pool returns no rows."""
    from kinetic.db.postgres_client import PostgresClient

    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock(return_value=False)
        )
    )

    client = PostgresClient(mock_pool, tenant="test")
    result = await client.get_burnout_series()
    assert result == []


@pytest.mark.unit
async def test_postgres_get_burnout_series_returns_float_list(tmp_path: Path) -> None:
    """PostgresClient.get_burnout_series() converts rows to burnout floats."""
    from kinetic.db.postgres_client import PostgresClient

    mock_row = {"sleep_hours": 6.0, "nutrition_quality": 7, "energy_level": 6}

    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[mock_row])

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_conn), __aexit__=AsyncMock(return_value=False)
        )
    )

    client = PostgresClient(mock_pool, tenant="test")
    result = await client.get_burnout_series()
    assert len(result) == 1
    assert isinstance(result[0], float)
    assert result[0] == pytest.approx(43.33, abs=0.1)
