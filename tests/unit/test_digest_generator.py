"""Unit tests for generate_digest() service — cache, TTL, empty guard, error recovery."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import kinetic.services.digest_generator as dg
from kinetic.db.base import DatabaseClient
from kinetic.models.outputs import BehavioralSummary, DigestResponse

# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Isolate each test — clear the module-level cache before and after."""
    dg._digest_cache.clear()
    yield  # type: ignore[misc]
    dg._digest_cache.clear()


def _make_summary(days_analyzed: int = 5) -> BehavioralSummary:
    return BehavioralSummary(
        bio_trend=None,
        recurring_tasks=[],
        relational_drifts=[],
        days_analyzed=days_analyzed,
        generated_at=datetime.now(),
    )


def _make_db(
    days_analyzed: int = 5,
    history: list[dict[str, str]] | None = None,
) -> AsyncMock:
    db: AsyncMock = AsyncMock(spec=DatabaseClient)
    db.get_behavioral_summary.return_value = _make_summary(days_analyzed)
    db.get_behavioral_profiles.return_value = []
    db.get_history.return_value = (
        [{"role": "user", "content": "slept 6 hours"}] if history is None else history
    )
    return db


def _mock_genai(text: str = "Your 14-day digest summary.") -> MagicMock:
    mock_response = MagicMock()
    mock_response.text = text
    mock_cls = MagicMock()
    mock_cls.return_value.models.generate_content.return_value = mock_response
    return mock_cls


# ── happy path ────────────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_generate_digest_calls_gemini_and_returns_response() -> None:
    """First call with data invokes Gemini and returns a populated DigestResponse."""
    db = _make_db()
    mock_cls = _mock_genai("Your 14-day digest.")

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-a")

    assert isinstance(result, DigestResponse)
    assert result.summary == "Your 14-day digest."
    assert isinstance(result.generated_at, datetime)
    mock_cls.return_value.models.generate_content.assert_called_once()


@pytest.mark.unit
async def test_generate_digest_stores_result_in_cache() -> None:
    """After a successful call the result is stored in _digest_cache under the tenant key."""
    db = _make_db()
    mock_cls = _mock_genai("Cached digest.")

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-b")

    assert "tenant-b" in dg._digest_cache
    assert dg._digest_cache["tenant-b"].summary == "Cached digest."
    assert dg._digest_cache["tenant-b"] is result


# ── cache behaviour ───────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_generate_digest_cache_hit_skips_gemini() -> None:
    """A fresh cached entry is returned immediately without calling Gemini."""
    dg._digest_cache["tenant-c"] = DigestResponse(
        summary="cached",
        generated_at=datetime.now(),
    )
    db = _make_db()
    mock_cls = _mock_genai()

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-c")

    assert result.summary == "cached"
    mock_cls.return_value.models.generate_content.assert_not_called()


@pytest.mark.unit
async def test_generate_digest_cache_miss_after_ttl_calls_gemini() -> None:
    """An expired cache entry (> 6h old) causes Gemini to be called again."""
    old_time = datetime.now() - timedelta(hours=7)
    dg._digest_cache["tenant-d"] = DigestResponse(summary="old", generated_at=old_time)

    db = _make_db()
    mock_cls = _mock_genai("fresh digest")

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-d")

    assert result.summary == "fresh digest"
    mock_cls.return_value.models.generate_content.assert_called_once()


@pytest.mark.unit
async def test_generate_digest_force_true_bypasses_fresh_cache() -> None:
    """force=True regenerates even when the cached entry is still within TTL."""
    dg._digest_cache["tenant-e"] = DigestResponse(
        summary="still fresh",
        generated_at=datetime.now(),
    )
    db = _make_db()
    mock_cls = _mock_genai("forced fresh")

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-e", force=True)

    assert result.summary == "forced fresh"
    mock_cls.return_value.models.generate_content.assert_called_once()


@pytest.mark.unit
async def test_generate_digest_force_true_updates_cache() -> None:
    """force=True replaces the cached entry with the newly generated digest."""
    dg._digest_cache["tenant-f"] = DigestResponse(
        summary="old cached",
        generated_at=datetime.now(),
    )
    db = _make_db()
    mock_cls = _mock_genai("new forced")

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        await dg.generate_digest(db, "test-key", "tenant-f", force=True)

    assert dg._digest_cache["tenant-f"].summary == "new forced"


# ── empty-history guard ───────────────────────────────────────────────────────


@pytest.mark.unit
async def test_generate_digest_empty_data_returns_canned_response() -> None:
    """days_analyzed == 0 and no history → canned response, Gemini never called."""
    db = _make_db(days_analyzed=0, history=[])
    mock_cls = _mock_genai()

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-g")

    assert "No check-in data" in result.summary
    mock_cls.return_value.models.generate_content.assert_not_called()


@pytest.mark.unit
async def test_generate_digest_has_history_but_no_bio_still_calls_gemini() -> None:
    """days_analyzed == 0 but history exists → guard does NOT fire, Gemini is called."""
    db = _make_db(days_analyzed=0, history=[{"role": "user", "content": "hello"}])
    mock_cls = _mock_genai("digest from history only")

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-h")

    assert result.summary == "digest from history only"
    mock_cls.return_value.models.generate_content.assert_called_once()


# ── error recovery ────────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_generate_digest_gemini_exception_returns_error_string() -> None:
    """A Gemini exception is caught; result summary begins with [DIGEST ERROR]."""
    db = _make_db()
    mock_cls = MagicMock()
    mock_cls.return_value.models.generate_content.side_effect = RuntimeError("timeout")

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-i")

    assert result.summary.startswith("[DIGEST ERROR]")
    assert "timeout" in result.summary
    assert isinstance(result.generated_at, datetime)


@pytest.mark.unit
async def test_generate_digest_gemini_exception_does_not_raise() -> None:
    """A Gemini exception never propagates — generate_digest always returns DigestResponse."""
    db = _make_db()
    mock_cls = MagicMock()
    mock_cls.return_value.models.generate_content.side_effect = OSError("network")

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-j")

    assert isinstance(result, DigestResponse)
