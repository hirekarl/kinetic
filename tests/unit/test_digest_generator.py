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
    mock_cls.return_value.aio.models.generate_content = AsyncMock(return_value=mock_response)
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
    mock_cls.return_value.aio.models.generate_content.assert_called_once()


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
    mock_cls.return_value.aio.models.generate_content.assert_not_called()


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
    mock_cls.return_value.aio.models.generate_content.assert_called_once()


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
    mock_cls.return_value.aio.models.generate_content.assert_called_once()


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
    mock_cls.return_value.aio.models.generate_content.assert_not_called()


@pytest.mark.unit
async def test_generate_digest_has_history_but_no_bio_still_calls_gemini() -> None:
    """days_analyzed == 0 but history exists → guard does NOT fire, Gemini is called."""
    db = _make_db(days_analyzed=0, history=[{"role": "user", "content": "hello"}])
    mock_cls = _mock_genai("digest from history only")

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-h")

    assert result.summary == "digest from history only"
    mock_cls.return_value.aio.models.generate_content.assert_called_once()


# ── error recovery ────────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_generate_digest_gemini_exception_returns_error_string() -> None:
    """A Gemini exception is caught; result summary begins with [DIGEST ERROR]."""
    db = _make_db()
    mock_cls = MagicMock()
    mock_cls.return_value.aio.models.generate_content = AsyncMock(
        side_effect=RuntimeError("timeout")
    )

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
    mock_cls.return_value.aio.models.generate_content = AsyncMock(
        side_effect=OSError("network")
    )

    with patch("kinetic.services.digest_generator.genai.Client", mock_cls):
        result = await dg.generate_digest(db, "test-key", "tenant-j")

    assert isinstance(result, DigestResponse)


# ── _build_digest_prompt formatting branches ──────────────────────────────────


@pytest.mark.unit
def test_build_digest_prompt_includes_bio_trend_stats() -> None:
    """Prompt contains sleep avg and slope when bio_trend is populated."""
    from kinetic.models.outputs import BioTrend
    from kinetic.services.digest_generator import _build_digest_prompt

    summary = BehavioralSummary(
        bio_trend=BioTrend(
            avg_sleep_hours=6.2,
            sleep_slope=-0.25,
            avg_nutrition=7.0,
            avg_energy=6.5,
            sleep_series=[7.0, 6.5, 6.0],
            days_analyzed=3,
        ),
        recurring_tasks=[],
        relational_drifts=[],
        days_analyzed=3,
        generated_at=datetime.now(),
    )
    prompt = _build_digest_prompt(summary, [], [])

    assert "6.2" in prompt
    assert "-0.25" in prompt


@pytest.mark.unit
def test_build_digest_prompt_includes_worst_sleep_day() -> None:
    """Prompt includes worst_sleep_day when set."""
    from kinetic.models.outputs import BioTrend
    from kinetic.services.digest_generator import _build_digest_prompt

    summary = BehavioralSummary(
        bio_trend=BioTrend(
            avg_sleep_hours=6.0,
            sleep_slope=-0.1,
            avg_nutrition=7.0,
            avg_energy=6.0,
            sleep_series=[6.0],
            days_analyzed=1,
            worst_sleep_day="2026-04-28",
        ),
        recurring_tasks=[],
        relational_drifts=[],
        days_analyzed=1,
        generated_at=datetime.now(),
    )
    prompt = _build_digest_prompt(summary, [], [])

    assert "2026-04-28" in prompt


@pytest.mark.unit
def test_build_digest_prompt_no_bio_uses_placeholder() -> None:
    """Prompt says 'No bio data' when bio_trend is None."""
    from kinetic.services.digest_generator import _build_digest_prompt

    summary = BehavioralSummary(
        bio_trend=None,
        recurring_tasks=[],
        relational_drifts=[],
        days_analyzed=0,
        generated_at=datetime.now(),
    )
    prompt = _build_digest_prompt(summary, [], [])

    assert "No bio data" in prompt


@pytest.mark.unit
def test_build_digest_prompt_includes_recurring_tasks() -> None:
    """Prompt includes recurring task names and counts when tasks are present."""
    from kinetic.models.outputs import RecurringTask
    from kinetic.services.digest_generator import _build_digest_prompt

    summary = BehavioralSummary(
        bio_trend=None,
        recurring_tasks=[
            RecurringTask(name="laundry", times_overdue=3, avg_days_overdue=4.5, priority="high")
        ],
        relational_drifts=[],
        days_analyzed=7,
        generated_at=datetime.now(),
    )
    prompt = _build_digest_prompt(summary, [], [])

    assert "laundry" in prompt
    assert "3" in prompt


@pytest.mark.unit
def test_build_digest_prompt_no_tasks_uses_placeholder() -> None:
    """Prompt says 'No recurring overdue tasks' when list is empty."""
    from kinetic.services.digest_generator import _build_digest_prompt

    summary = BehavioralSummary(
        bio_trend=None,
        recurring_tasks=[],
        relational_drifts=[],
        days_analyzed=0,
        generated_at=datetime.now(),
    )
    prompt = _build_digest_prompt(summary, [], [])

    assert "No recurring overdue tasks" in prompt


@pytest.mark.unit
def test_build_digest_prompt_includes_relational_drifts() -> None:
    """Prompt includes drifting contact names when relational_drifts are present."""
    from kinetic.models.outputs import RelationalDrift
    from kinetic.services.digest_generator import _build_digest_prompt

    summary = BehavioralSummary(
        bio_trend=None,
        recurring_tasks=[],
        relational_drifts=[
            RelationalDrift(
                person="Marcus",
                contact_trend=1.5,
                avg_vibe_score=5.5,
                last_known_days_since_contact=9,
            )
        ],
        days_analyzed=7,
        generated_at=datetime.now(),
    )
    prompt = _build_digest_prompt(summary, [], [])

    assert "Marcus" in prompt
    assert "1.5" in prompt or "+1.50" in prompt


@pytest.mark.unit
def test_build_digest_prompt_no_drifts_uses_placeholder() -> None:
    """Prompt says 'No relational drifts detected' when list is empty."""
    from kinetic.services.digest_generator import _build_digest_prompt

    summary = BehavioralSummary(
        bio_trend=None,
        recurring_tasks=[],
        relational_drifts=[],
        days_analyzed=0,
        generated_at=datetime.now(),
    )
    prompt = _build_digest_prompt(summary, [], [])

    assert "No relational drifts detected" in prompt


@pytest.mark.unit
def test_build_digest_prompt_includes_behavioral_profiles() -> None:
    """Prompt includes profile insights when profiles list is non-empty."""
    from kinetic.models.outputs import BehavioralProfile
    from kinetic.services.digest_generator import _build_digest_prompt

    now = datetime.now()
    profiles = [
        BehavioralProfile(
            profile_key="sleep_deficit",
            insight="Consistently sleeps under 6 hours on weekdays.",
            evidence={},
            first_observed=now,
            last_updated=now,
            observation_count=5,
        )
    ]
    summary = BehavioralSummary(
        bio_trend=None,
        recurring_tasks=[],
        relational_drifts=[],
        days_analyzed=0,
        generated_at=now,
    )
    prompt = _build_digest_prompt(summary, profiles, [])

    assert "sleep_deficit" in prompt
    assert "6 hours" in prompt
