"""Unit tests for OperationalLiaison — including behavioral context enrichment."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from kinetic.agents.operational_liaison import OperationalLiaison
from kinetic.models.outputs import (
    BehavioralProfile,
    BehavioralSummary,
    BioTrend,
    TriageItem,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 4, 26, 12, 0, 0)


def _liaison() -> OperationalLiaison:
    return OperationalLiaison(api_key="test-key")


def _mock_genai(response_text: str = "Tactical feedback.") -> MagicMock:
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_instance = MagicMock()
    mock_instance.models.generate_content.return_value = mock_response
    return mock_instance


def _triage() -> list[TriageItem]:
    return [
        TriageItem(
            id="bio-000",
            priority=8,
            domain="bio",
            description="Sleep deficit",
            action="Hard stop at 11pm",
        )
    ]


def _summary() -> BehavioralSummary:
    return BehavioralSummary(
        bio_trend=BioTrend(
            avg_sleep_hours=5.9,
            sleep_slope=-0.3,
            avg_nutrition=6.0,
            avg_energy=5.5,
            worst_sleep_day="2026-04-24",
            days_analyzed=7,
        ),
        recurring_tasks=[],
        relational_drifts=[],
        days_analyzed=7,
        generated_at=_NOW,
    )


def _profile() -> BehavioralProfile:
    return BehavioralProfile(
        profile_key="sleep_deficit",
        insight="Consistently undersleeps before high-workload days.",
        evidence={"avg_sleep": 5.9},
        first_observed=_NOW,
        last_updated=_NOW,
        observation_count=3,
    )


# ── Basic behaviour ───────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_process_without_behavioral_context() -> None:
    """Works with no behavioral data — original three-param call still valid."""
    mock_instance = _mock_genai()
    with patch("kinetic.agents.operational_liaison.genai.Client", return_value=mock_instance):
        result = await _liaison().process(
            message="Feeling tired.",
            overall_status="yellow",
            triage_items=_triage(),
        )

    assert isinstance(result, str)
    assert len(result) > 0
    mock_instance.models.generate_content.assert_called_once()


@pytest.mark.unit
async def test_process_returns_fallback_on_gemini_failure() -> None:
    """Gemini exception → returns fallback string, never raises."""
    mock_instance = MagicMock()
    mock_instance.models.generate_content.side_effect = RuntimeError("API down")
    with patch("kinetic.agents.operational_liaison.genai.Client", return_value=mock_instance):
        result = await _liaison().process(
            message="Check-in.",
            overall_status="green",
            triage_items=[],
        )

    assert "SYSTEM ERROR" in result or "offline" in result.lower()


# ── Behavioral context enrichment ─────────────────────────────────────────────


@pytest.mark.unit
async def test_process_with_summary_passes_bio_trend_to_gemini() -> None:
    """When behavioral_summary is provided, the Gemini prompt contains sleep trend data."""
    mock_instance = _mock_genai()
    summary = _summary()

    with patch("kinetic.agents.operational_liaison.genai.Client", return_value=mock_instance):
        await _liaison().process(
            message="Tired.",
            overall_status="yellow",
            triage_items=[],
            behavioral_summary=summary,
        )

    call_args = mock_instance.models.generate_content.call_args
    prompt_text = str(call_args)
    assert "5.9" in prompt_text or "sleep" in prompt_text.lower()


@pytest.mark.unit
async def test_process_with_profiles_passes_insights_to_gemini() -> None:
    """When behavioral_profiles are provided, existing insights appear in the Gemini prompt."""
    mock_instance = _mock_genai()
    profile = _profile()

    with patch("kinetic.agents.operational_liaison.genai.Client", return_value=mock_instance):
        await _liaison().process(
            message="Check-in.",
            overall_status="green",
            triage_items=[],
            behavioral_profiles=[profile],
        )

    call_args = mock_instance.models.generate_content.call_args
    prompt_text = str(call_args)
    assert "sleep_deficit" in prompt_text or "Consistently undersleeps" in prompt_text


@pytest.mark.unit
async def test_process_with_both_context_types_succeeds() -> None:
    """Summary + profiles together produce a valid string response."""
    mock_instance = _mock_genai("Prioritize sleep. Drop non-critical tasks tonight.")

    with patch("kinetic.agents.operational_liaison.genai.Client", return_value=mock_instance):
        result = await _liaison().process(
            message="Exhausted.",
            overall_status="red",
            triage_items=_triage(),
            behavioral_summary=_summary(),
            behavioral_profiles=[_profile()],
        )

    assert isinstance(result, str)
    assert len(result) > 0
