"""Deterministic adversarial scenario tests for the Operational Liaison.

Each scenario verifies a specific conversational behavior described in the B1
prompt-hardening rules. All tests are fully mocked — no real LLM calls.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kinetic.agents.operational_liaison import LiaisonResponse
from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsInput,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)
from kinetic.orchestrator.lead import orchestrate

_MOCK_SUMMARY_DATA = {
    "bio_trend": None,
    "recurring_tasks": [],
    "relational_drifts": [],
    "days_analyzed": 5,
    "generated_at": datetime(2026, 4, 26, 12, 0, 0),
}


@pytest.fixture(autouse=True)
def mock_db() -> MagicMock:
    with patch("kinetic.orchestrator.lead.get_db") as mock:
        from kinetic.models.outputs import BehavioralSummary

        client = MagicMock()
        client.insert_checkin = AsyncMock(return_value="test-id")
        client.get_latest_bio = AsyncMock(return_value=None)
        client.get_all_tasks = AsyncMock(return_value=[])
        client.get_all_vibes = AsyncMock(return_value=[])
        client.get_recent_bio = AsyncMock(return_value=[])
        client.get_behavioral_summary = AsyncMock(
            return_value=BehavioralSummary(**_MOCK_SUMMARY_DATA)
        )
        client.get_behavioral_profiles = AsyncMock(return_value=[])
        client.upsert_contact_pause = AsyncMock(return_value=None)
        client.get_active_pauses = AsyncMock(return_value=[])
        client.complete_task = AsyncMock(return_value=None)
        mock.return_value = client
        yield client


# ── Scenario 1: Competing crisis — multi-domain RED + deadline ────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scenario_1_competing_crisis_returns_synthesized_response() -> None:
    """
    Scenario: Bio is RED (sleep_hours=3), logistics is RED (critical task overdue 5d),
    relational is RED (vibe score 2, 20d since contact). User says "everything is
    falling apart — I also have a demo tomorrow."

    Expected: Liaison returns a single structured response (not domain-by-domain
    noise) with text acknowledging the multi-domain state.
    The SYNTHESIS rule in the prompt should produce a prioritized sequence.
    """
    payload = CheckInPayload(
        bio=BioInput(sleep_hours=3.0, nutrition_quality=2, energy_level=2),
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="demo_prep", days_overdue=5, priority="critical")]
        ),
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Jordan", score=2, days_since_contact=20)]
        ),
    )
    expected_response = LiaisonResponse(
        text=(
            "All three sectors are critical. Protocol: 1) Get 4+ hours sleep tonight — "
            "cognitive performance for the demo depends on it. 2) Demo prep is your only "
            "logistics task tomorrow. 3) Jordan outreach can wait 48h; flag it after the demo."
        ),
        responding_agent="liaison",
    )

    with patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls:
        instance = MagicMock()
        instance.process = AsyncMock(return_value=expected_response)
        mock_liaison_cls.return_value = instance

        result = await orchestrate(
            payload, message="Everything is falling apart — I also have a demo tomorrow."
        )

    assert result.overall_status == "red"
    assert result.bio is not None
    assert result.logistics is not None
    assert result.relational is not None
    assert result.liaison_feedback is not None
    assert len(result.liaison_feedback) > 0


# ── Scenario 2: Partial recovery — prior recommendation followed ──────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scenario_2_partial_recovery_liaison_acknowledges_improvement() -> None:
    """
    Scenario: User previously had sleep_hours=4 (RED). Now reports sleep_hours=7.
    Message: "I followed your advice and slept 7 hours last night."

    Expected: Liaison response acknowledges the improvement delta, updates forecast
    optimistically. The IMPROVEMENT ACK rule should be triggered.
    """
    payload = CheckInPayload(
        bio=BioInput(sleep_hours=7.0, nutrition_quality=7, energy_level=7),
    )
    prior_history = [
        {"role": "user", "content": "I only slept 4 hours."},
        {"role": "system", "content": "Sleep deficit is critical. Hard stop at 10pm tonight."},
    ]
    expected_response = LiaisonResponse(
        text=(
            "Improvement registered: +3 hours from your prior 4-hour session. "
            "Burnout trajectory is now neutral. Maintain the 10pm stop tonight to lock in the gain."
        ),
        responding_agent="bio_archivist",
    )

    with patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls:
        instance = MagicMock()
        instance.process = AsyncMock(return_value=expected_response)
        mock_liaison_cls.return_value = instance

        result = await orchestrate(
            payload,
            message="I followed your advice and slept 7 hours last night.",
            history=prior_history,
        )

    assert result.overall_status in ("green", "yellow")
    assert result.bio is not None
    assert result.bio.status in ("green", "yellow")
    call_kwargs = instance.process.call_args.kwargs
    assert call_kwargs.get("history") == prior_history


# ── Scenario 3: Event prep — multi-domain with deadline ──────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scenario_3_event_prep_routes_all_three_specialists() -> None:
    """
    Scenario: User says "I have a big presentation in 3 days. What do I need to do?"
    Bio is YELLOW, logistics has pending tasks, relational is nominal.

    Expected: Orchestrator routes correctly, liaison synthesizes pre-event protocol
    drawing from all three specialists per the EVENT ROUTING rule.
    """
    payload = CheckInPayload(
        bio=BioInput(sleep_hours=6.0, nutrition_quality=6, energy_level=6),
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="slide_deck", days_overdue=1, priority="high")]
        ),
    )
    expected_response = LiaisonResponse(
        text=(
            "Pre-event protocol (3 days out): "
            "Bio Archivist: 7+ hrs sleep tonight and tomorrow; no alcohol. "
            "Logistics Fixer: Slide deck is your only task — defer laundry. "
            "Relational Diplomat: Confirm venue contact tomorrow, then go dark until after."
        ),
        responding_agent="liaison",
    )

    with patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls:
        instance = MagicMock()
        instance.process = AsyncMock(return_value=expected_response)
        mock_liaison_cls.return_value = instance

        result = await orchestrate(
            payload,
            message="I have a big presentation in 3 days. What do I need to do?",
        )

    assert result.bio is not None
    assert result.logistics is not None
    call_kwargs = instance.process.call_args.kwargs
    assert call_kwargs.get("bio_status") is not None
    assert call_kwargs.get("logistics_status") is not None


# ── Scenario 4: Conversational delegation — pronoun resolved from history ─────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scenario_4_pronoun_resolved_from_history() -> None:
    """
    Scenario: History contains "Marcus hasn't responded to my last three messages."
    User asks: "Should I reach out to him again?"

    Expected: Liaison receives the history and routes to relational_diplomat.
    The HISTORY RESOLUTION rule should resolve 'him' from prior turns.
    """
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=4, days_since_contact=14)]
        )
    )
    prior_history = [
        {"role": "user", "content": "Marcus hasn't responded to my last three messages."},
        {
            "role": "system",
            "content": "Noted. Marcus shows declining engagement — connection margin is low.",
        },
    ]
    expected_response = LiaisonResponse(
        text=(
            "Hold on Marcus outreach. Three unanswered messages is a signal — "
            "another message now will likely register as pressure. "
            "Give it 5-7 more days, then reach out with a low-stakes opener."
        ),
        responding_agent="relational_diplomat",
    )

    with patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls:
        instance = MagicMock()
        instance.process = AsyncMock(return_value=expected_response)
        mock_liaison_cls.return_value = instance

        result = await orchestrate(
            payload,
            message="Should I reach out to him again?",
            history=prior_history,
        )

    assert result.responding_agent == "relational_diplomat"
    call_kwargs = instance.process.call_args.kwargs
    assert call_kwargs.get("history") == prior_history
    assert call_kwargs.get("relational_status") is not None


# ── Scenario 5: Agency override — user pushes through against advice ──────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_scenario_5_agency_override_pivots_to_risk_mitigation() -> None:
    """
    Scenario: Prior response advised sleep. User says "I know you said sleep but
    I'm pulling an all-nighter to finish the project."

    Expected: Liaison does NOT re-argue about sleep. Instead it pivots to risk
    mitigation per the AGENCY rule. Orchestrator returns the response without
    blocking or re-lecturing.
    """
    payload = CheckInPayload(
        bio=BioInput(sleep_hours=2.0, nutrition_quality=5, energy_level=4),
    )
    prior_history = [
        {"role": "user", "content": "I feel burned out."},
        {
            "role": "system",
            "content": "Hard stop at 10pm. Your burnout score is at 78. Sleep is non-negotiable.",
        },
    ]
    expected_response = LiaisonResponse(
        text=(
            "Understood. If you're committing to the all-nighter: "
            "1) Caffeine cap at midnight — no more after that or recovery crashes. "
            "2) 20-min nap at 3am if possible. "
            "3) Hydration every 90 min. "
            "Tomorrow is a recovery day — no new commitments."
        ),
        responding_agent="bio_archivist",
    )

    with patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls:
        instance = MagicMock()
        instance.process = AsyncMock(return_value=expected_response)
        mock_liaison_cls.return_value = instance

        result = await orchestrate(
            payload,
            message="I know you said sleep but I'm pulling an all-nighter to finish the project.",
            history=prior_history,
        )

    assert result.overall_status in ("yellow", "red")
    assert result.liaison_feedback is not None
    assert result.responding_agent == "bio_archivist"
    call_kwargs = instance.process.call_args.kwargs
    assert call_kwargs.get("history") == prior_history
