"""Unit tests for the Pattern Detector background service."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kinetic.models.outputs import (
    BehavioralProfile,
    BehavioralSummary,
    BioTrend,
)
from kinetic.services.pattern_detector import detect_and_update_patterns

# ── Fixtures ─────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 4, 26, 12, 0, 0)


def _summary(days: int = 5) -> BehavioralSummary:
    """Minimal BehavioralSummary with configurable days_analyzed."""
    return BehavioralSummary(
        bio_trend=BioTrend(
            avg_sleep_hours=6.2,
            sleep_slope=-0.2,
            avg_nutrition=6.5,
            avg_energy=5.8,
            worst_sleep_day="2026-04-24",
            days_analyzed=days,
        ),
        recurring_tasks=[],
        relational_drifts=[],
        days_analyzed=days,
        generated_at=_NOW,
    )


def _old_profile(key: str = "sleep_deficit") -> BehavioralProfile:
    """A profile last updated 25 hours ago — outside the 20-hour guard window."""
    ts = _NOW - timedelta(hours=25)
    return BehavioralProfile(
        profile_key=key,
        insight="Existing insight.",
        evidence={},
        first_observed=ts,
        last_updated=ts,
        observation_count=1,
    )


def _recent_profile(key: str = "sleep_deficit") -> BehavioralProfile:
    """A profile last updated 5 hours ago — inside the 20-hour guard window."""
    ts = _NOW - timedelta(hours=5)
    return BehavioralProfile(
        profile_key=key,
        insight="Recent insight.",
        evidence={},
        first_observed=ts,
        last_updated=ts,
        observation_count=2,
    )


def _mock_db(upsert_side_effect: Exception | None = None) -> AsyncMock:
    db = AsyncMock()
    if upsert_side_effect:
        db.upsert_behavioral_profile.side_effect = upsert_side_effect
    return db


def _gemini_response(patterns: list[dict]) -> MagicMock:
    """Build a mock Gemini response containing a JSON array of patterns."""
    mock = MagicMock()
    mock.text = json.dumps(patterns)
    return mock


# ── Rate-limit guard tests ────────────────────────────────────────────────────


@pytest.mark.unit
async def test_guard_insufficient_history() -> None:
    """Skip when days_analyzed < 3 — no Gemini call, no DB write."""
    db = _mock_db()
    with patch("kinetic.services.pattern_detector.genai.Client") as mock_client_cls:
        await detect_and_update_patterns(db, _summary(days=2), [], api_key="test-key")

    mock_client_cls.assert_not_called()
    db.upsert_behavioral_profile.assert_not_called()


@pytest.mark.unit
async def test_guard_recently_updated_profile() -> None:
    """Skip when any profile was updated within the last 20 hours."""
    db = _mock_db()
    profiles = [_recent_profile()]
    with patch("kinetic.services.pattern_detector.genai.Client") as mock_client_cls:
        await detect_and_update_patterns(db, _summary(days=5), profiles, api_key="test-key")

    mock_client_cls.assert_not_called()
    db.upsert_behavioral_profile.assert_not_called()


@pytest.mark.unit
async def test_guard_passes_when_profiles_are_old() -> None:
    """Gemini IS called when days_analyzed >= 3 and all profiles are > 20h old."""
    db = _mock_db()
    mock_instance = MagicMock()
    mock_instance.models.generate_content.return_value = _gemini_response([])

    with patch("kinetic.services.pattern_detector.genai.Client", return_value=mock_instance):
        await detect_and_update_patterns(db, _summary(days=5), [_old_profile()], api_key="test-key")

    mock_instance.models.generate_content.assert_called_once()


# ── Happy path tests ──────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_one_valid_pattern_upserted() -> None:
    """A single valid Gemini pattern is upserted to the DB."""
    db = _mock_db()
    pattern = {
        "profile_key": "sleep_deficit_pattern",
        "insight": "Consistently sleeps under 7 hours.",
        "evidence": {"avg_sleep": 6.2},
    }
    mock_instance = MagicMock()
    mock_instance.models.generate_content.return_value = _gemini_response([pattern])

    with patch("kinetic.services.pattern_detector.genai.Client", return_value=mock_instance):
        await detect_and_update_patterns(db, _summary(), [], api_key="test-key")

    db.upsert_behavioral_profile.assert_called_once()
    call_arg: BehavioralProfile = db.upsert_behavioral_profile.call_args[0][0]
    assert call_arg.profile_key == "sleep_deficit_pattern"
    assert "7 hours" in call_arg.insight


@pytest.mark.unit
async def test_two_valid_patterns_upserted() -> None:
    """Two valid patterns both get upserted."""
    db = _mock_db()
    patterns = [
        {"profile_key": "sleep_deficit", "insight": "Under-sleeping.", "evidence": {}},
        {"profile_key": "work_boundary", "insight": "Late nights.", "evidence": {"count": 4}},
    ]
    mock_instance = MagicMock()
    mock_instance.models.generate_content.return_value = _gemini_response(patterns)

    with patch("kinetic.services.pattern_detector.genai.Client", return_value=mock_instance):
        await detect_and_update_patterns(db, _summary(), [], api_key="test-key")

    assert db.upsert_behavioral_profile.call_count == 2


@pytest.mark.unit
async def test_existing_profile_key_still_upserted() -> None:
    """Upsert is called even when profile_key already exists — DB handles idempotency."""
    db = _mock_db()
    existing = _old_profile("sleep_deficit")
    pattern = {
        "profile_key": "sleep_deficit",
        "insight": "Updated insight from new data.",
        "evidence": {"avg_sleep": 6.0},
    }
    mock_instance = MagicMock()
    mock_instance.models.generate_content.return_value = _gemini_response([pattern])

    with patch("kinetic.services.pattern_detector.genai.Client", return_value=mock_instance):
        await detect_and_update_patterns(db, _summary(), [existing], api_key="test-key")

    db.upsert_behavioral_profile.assert_called_once()


# ── Exception safety tests ────────────────────────────────────────────────────


@pytest.mark.unit
async def test_gemini_exception_does_not_propagate() -> None:
    """If Gemini raises, the function catches and returns — never re-raises."""
    db = _mock_db()
    mock_instance = MagicMock()
    mock_instance.models.generate_content.side_effect = RuntimeError("API down")

    with patch("kinetic.services.pattern_detector.genai.Client", return_value=mock_instance):
        # Must not raise
        await detect_and_update_patterns(db, _summary(), [], api_key="test-key")

    db.upsert_behavioral_profile.assert_not_called()


@pytest.mark.unit
async def test_malformed_json_does_not_propagate() -> None:
    """Unparseable Gemini response is caught and logged — function returns normally."""
    db = _mock_db()
    mock_instance = MagicMock()
    bad_response = MagicMock()
    bad_response.text = "This is not JSON at all { broken"
    mock_instance.models.generate_content.return_value = bad_response

    with patch("kinetic.services.pattern_detector.genai.Client", return_value=mock_instance):
        await detect_and_update_patterns(db, _summary(), [], api_key="test-key")

    db.upsert_behavioral_profile.assert_not_called()


@pytest.mark.unit
async def test_wrong_shape_skips_bad_entries_upserts_good() -> None:
    """Missing profile_key skips that entry; valid entries still upserted."""
    db = _mock_db()
    patterns = [
        {"insight": "No key here.", "evidence": {}},  # missing profile_key — skip
        {"profile_key": "valid_pattern", "insight": "Good one.", "evidence": {}},
    ]
    mock_instance = MagicMock()
    mock_instance.models.generate_content.return_value = _gemini_response(patterns)

    with patch("kinetic.services.pattern_detector.genai.Client", return_value=mock_instance):
        await detect_and_update_patterns(db, _summary(), [], api_key="test-key")

    assert db.upsert_behavioral_profile.call_count == 1
    call_arg: BehavioralProfile = db.upsert_behavioral_profile.call_args[0][0]
    assert call_arg.profile_key == "valid_pattern"


@pytest.mark.unit
async def test_upsert_exception_does_not_propagate() -> None:
    """If upsert_behavioral_profile raises, it is caught — function returns normally."""
    db = _mock_db(upsert_side_effect=OSError("DB write failed"))
    pattern = {
        "profile_key": "sleep_deficit",
        "insight": "Sleeps too little.",
        "evidence": {},
    }
    mock_instance = MagicMock()
    mock_instance.models.generate_content.return_value = _gemini_response([pattern])

    with patch("kinetic.services.pattern_detector.genai.Client", return_value=mock_instance):
        # Must not raise
        await detect_and_update_patterns(db, _summary(), [], api_key="test-key")


# ── _build_prompt branches ────────────────────────────────────────────────────


@pytest.mark.unit
def test_build_prompt_includes_recurring_tasks() -> None:
    """_build_prompt includes recurring task lines when summary has recurring_tasks."""
    from kinetic.models.outputs import RecurringTask
    from kinetic.services.pattern_detector import _build_prompt

    summary = BehavioralSummary(
        bio_trend=_summary().bio_trend,
        recurring_tasks=[
            RecurringTask(name="laundry", times_overdue=3, avg_days_overdue=4.5, priority="high")
        ],
        relational_drifts=[],
        days_analyzed=5,
        generated_at=_NOW,
    )
    prompt = _build_prompt(summary, [])

    assert "laundry" in prompt
    assert "3x" in prompt or "3)" in prompt


@pytest.mark.unit
def test_build_prompt_includes_relational_drifts() -> None:
    """_build_prompt includes relational drift lines when summary has relational_drifts."""
    from kinetic.models.outputs import RelationalDrift
    from kinetic.services.pattern_detector import _build_prompt

    summary = BehavioralSummary(
        bio_trend=_summary().bio_trend,
        recurring_tasks=[],
        relational_drifts=[
            RelationalDrift(
                person="Marcus",
                contact_trend=1.5,
                avg_vibe_score=5.5,
                last_known_days_since_contact=9,
            )
        ],
        days_analyzed=5,
        generated_at=_NOW,
    )
    prompt = _build_prompt(summary, [])

    assert "Marcus" in prompt
    assert "+1.50" in prompt


# ── _parse_patterns edge cases ────────────────────────────────────────────────


@pytest.mark.unit
def test_parse_patterns_raises_on_unmatched_bracket() -> None:
    """_parse_patterns raises ValueError when brackets are unmatched (no opening '[')."""
    from kinetic.services.pattern_detector import _parse_patterns

    with pytest.raises(ValueError, match="Unmatched brackets"):
        _parse_patterns("no opening bracket here ]")


@pytest.mark.unit
async def test_non_dict_entry_in_response_is_skipped() -> None:
    """A non-dict entry in Gemini's JSON array is skipped via _is_valid_entry."""
    db = _mock_db()
    mock_instance = MagicMock()
    mock_instance.models.generate_content.return_value = _gemini_response(
        ["not_a_dict", {"profile_key": "valid", "insight": "Good.", "evidence": {}}]
    )

    with patch("kinetic.services.pattern_detector.genai.Client", return_value=mock_instance):
        await detect_and_update_patterns(db, _summary(), [], api_key="test-key")

    assert db.upsert_behavioral_profile.call_count == 1
