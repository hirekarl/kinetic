"""Unit tests for OperationalLiaison — including routing, behavioral context, and contact pauses."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from kinetic.agents.operational_liaison import (
    _HISTORY_WINDOW,
    ContactPauseDirective,
    LiaisonResponse,
    OperationalLiaison,
)
from kinetic.models.outputs import (
    BehavioralProfile,
    BehavioralSummary,
    BioStatus,
    BioTrend,
    LogisticsStatus,
    RelationalStatus,
    TriageItem,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 4, 26, 12, 0, 0)


def _liaison() -> OperationalLiaison:
    return OperationalLiaison(api_key="test-key")


@contextmanager
def _patch_liaison(
    response: LiaisonResponse | None = None,
) -> Generator[MagicMock, None, None]:
    """Patch genai.Client and instructor.from_genai; yield the mock Instructor client."""
    if response is None:
        response = LiaisonResponse(text="Tactical feedback.")
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = response
    with (
        patch("kinetic.agents.operational_liaison.genai.Client"),
        patch(
            "kinetic.agents.operational_liaison.instructor.from_genai",
            return_value=mock_client,
        ),
    ):
        yield mock_client


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
async def test_process_returns_liaison_response() -> None:
    """process() returns a LiaisonResponse with non-empty text."""
    with _patch_liaison() as mock_client:
        result = await _liaison().process(
            message="Feeling tired.",
            overall_status="yellow",
            triage_items=_triage(),
        )

    assert isinstance(result, LiaisonResponse)
    assert len(result.text) > 0
    mock_client.chat.completions.create.assert_called_once()


@pytest.mark.unit
async def test_process_returns_fallback_on_gemini_failure() -> None:
    """Instructor exception → returns LiaisonResponse with error text, never raises."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("API down")
    with (
        patch("kinetic.agents.operational_liaison.genai.Client"),
        patch(
            "kinetic.agents.operational_liaison.instructor.from_genai",
            return_value=mock_client,
        ),
    ):
        result = await _liaison().process(
            message="Check-in.",
            overall_status="green",
            triage_items=[],
        )

    assert isinstance(result, LiaisonResponse)
    assert "SYSTEM ERROR" in result.text or "offline" in result.text.lower()


# ── Behavioral context enrichment ─────────────────────────────────────────────


@pytest.mark.unit
async def test_process_with_summary_passes_bio_trend_to_llm() -> None:
    """When behavioral_summary is provided, the prompt contains sleep trend data."""
    with _patch_liaison() as mock_client:
        await _liaison().process(
            message="Tired.",
            overall_status="yellow",
            triage_items=[],
            behavioral_summary=_summary(),
        )

    call_args = mock_client.chat.completions.create.call_args
    messages_str = str(call_args)
    assert "5.9" in messages_str or "sleep" in messages_str.lower()


@pytest.mark.unit
async def test_process_with_profiles_passes_insights_to_llm() -> None:
    """When behavioral_profiles are provided, existing insights appear in the prompt."""
    with _patch_liaison() as mock_client:
        await _liaison().process(
            message="Check-in.",
            overall_status="green",
            triage_items=[],
            behavioral_profiles=[_profile()],
        )

    call_args = mock_client.chat.completions.create.call_args
    messages_str = str(call_args)
    assert "sleep_deficit" in messages_str or "Consistently undersleeps" in messages_str


@pytest.mark.unit
async def test_process_with_both_context_types_succeeds() -> None:
    """Summary + profiles together produce a valid LiaisonResponse."""
    with _patch_liaison(LiaisonResponse(text="Prioritize sleep. Drop non-critical tasks tonight.")):
        result = await _liaison().process(
            message="Exhausted.",
            overall_status="red",
            triage_items=_triage(),
            behavioral_summary=_summary(),
            behavioral_profiles=[_profile()],
        )

    assert isinstance(result, LiaisonResponse)
    assert len(result.text) > 0


# ── Rich agent context ────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_process_passes_bio_status_to_llm() -> None:
    """bio_status is included in the prompt so the LLM has specialist data."""
    bio = BioStatus(
        status="red", burnout_score=72, forecast="High burnout risk.", sleep_debt_hours=3.5
    )
    with _patch_liaison() as mock_client:
        await _liaison().process(
            message="What's my burnout score?",
            overall_status="red",
            triage_items=[],
            bio_status=bio,
        )

    messages_str = str(mock_client.chat.completions.create.call_args)
    assert "72" in messages_str or "burnout" in messages_str.lower()


@pytest.mark.unit
async def test_process_passes_logistics_status_to_llm() -> None:
    """logistics_status (including tasks with steps) is included in the prompt."""
    from kinetic.models.inputs import LogisticsTask

    logistics = LogisticsStatus(
        status="yellow",
        critical_tasks=["laundry"],
        tasks_with_steps=[
            LogisticsTask(name="laundry", priority="high", subtasks=["sort", "wash"])
        ],
        outsourcing_suggestions=["hire cleaner"],
        time_to_resolve_minutes=45,
    )
    with _patch_liaison() as mock_client:
        await _liaison().process(
            message="What should I outsource?",
            overall_status="yellow",
            triage_items=[],
            logistics_status=logistics,
        )

    messages_str = str(mock_client.chat.completions.create.call_args)
    assert "laundry" in messages_str.lower() or "outsource" in messages_str.lower()


@pytest.mark.unit
async def test_process_passes_relational_status_to_llm() -> None:
    """relational_status is included in the prompt."""
    relational = RelationalStatus(
        status="red",
        connection_margin_score=42,
        at_risk_relationships=["Marcus"],
        interaction_sprints=["Text Marcus"],
    )
    with _patch_liaison() as mock_client:
        await _liaison().process(
            message="How are my relationships?",
            overall_status="red",
            triage_items=[],
            relational_status=relational,
        )

    messages_str = str(mock_client.chat.completions.create.call_args)
    assert "Marcus" in messages_str or "42" in messages_str


# ── Specialist routing ────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_process_routes_to_bio_archivist() -> None:
    """Liaison response with bio_archivist agent is returned correctly."""
    response = LiaisonResponse(text="Your burnout is 72/100.", responding_agent="bio_archivist")
    with _patch_liaison(response):
        result = await _liaison().process(
            message="What's my burnout score?",
            overall_status="red",
            triage_items=[],
        )

    assert result.responding_agent == "bio_archivist"


@pytest.mark.unit
async def test_process_routes_to_logistics_fixer() -> None:
    """Liaison response with logistics_fixer agent is returned correctly."""
    response = LiaisonResponse(
        text="Laundry is your top priority.", responding_agent="logistics_fixer"
    )
    with _patch_liaison(response):
        result = await _liaison().process(
            message="What task should I do first?",
            overall_status="yellow",
            triage_items=[],
        )

    assert result.responding_agent == "logistics_fixer"


@pytest.mark.unit
async def test_process_routes_to_relational_diplomat() -> None:
    """Liaison response with relational_diplomat agent is returned correctly."""
    response = LiaisonResponse(
        text="Your connection margin is low.", responding_agent="relational_diplomat"
    )
    with _patch_liaison(response):
        result = await _liaison().process(
            message="How are my relationships?",
            overall_status="red",
            triage_items=[],
        )

    assert result.responding_agent == "relational_diplomat"


@pytest.mark.unit
async def test_process_defaults_to_liaison_agent() -> None:
    """Default responding_agent is 'liaison'."""
    with _patch_liaison():
        result = await _liaison().process(
            message="General status check.",
            overall_status="green",
            triage_items=[],
        )

    assert result.responding_agent == "liaison"


# ── Contact pauses ────────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_process_returns_contact_pause_directive() -> None:
    """Liaison response with contact_pauses is returned correctly."""
    response = LiaisonResponse(
        text="Contact pause noted for Marcus.",
        contact_pauses=[ContactPauseDirective(person="Marcus", pause_days=14)],
    )
    with _patch_liaison(response):
        result = await _liaison().process(
            message="Marcus and I are on a break for 2 weeks.",
            overall_status="green",
            triage_items=[],
        )

    assert len(result.contact_pauses) == 1
    assert result.contact_pauses[0].person == "Marcus"
    assert result.contact_pauses[0].pause_days == 14


@pytest.mark.unit
async def test_process_empty_contact_pauses_by_default() -> None:
    """Regular check-in produces no contact_pauses."""
    with _patch_liaison():
        result = await _liaison().process(
            message="Slept 7 hours, feeling good.",
            overall_status="green",
            triage_items=[],
        )

    assert result.contact_pauses == []


@pytest.mark.unit
async def test_process_returns_task_completions() -> None:
    """Liaison response with task_completions is returned correctly."""
    response = LiaisonResponse(
        text="Marked laundry complete.",
        task_completions=["laundry"],
    )
    with _patch_liaison(response):
        result = await _liaison().process(
            message="I just finished the laundry.",
            overall_status="green",
            triage_items=[],
        )

    assert result.task_completions == ["laundry"]


@pytest.mark.unit
async def test_process_empty_task_completions_by_default() -> None:
    """Regular check-in with no task completion mention produces no task_completions."""
    with _patch_liaison():
        result = await _liaison().process(
            message="Feeling tired.",
            overall_status="yellow",
            triage_items=[],
        )

    assert result.task_completions == []


# ── Conversation history ──────────────────────────────────────────────────────


@pytest.mark.unit
async def test_process_with_history_includes_prior_turns() -> None:
    """When history is provided, prior turns appear in the messages sent to the LLM."""
    history = [
        {"role": "user", "content": "Slept 4 hours."},
        {"role": "system", "content": "Sleep deficit detected."},
    ]
    with _patch_liaison() as mock_client:
        await _liaison().process(
            message="How do I recover my burnout?",
            overall_status="red",
            triage_items=_triage(),
            history=history,
        )

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    assert isinstance(messages, list)
    messages_str = str(messages)
    assert "Slept 4 hours" in messages_str
    assert "Sleep deficit detected" in messages_str


@pytest.mark.unit
async def test_process_without_history_still_uses_messages_list() -> None:
    """No history → messages is still a list containing at least the current turn."""
    with _patch_liaison() as mock_client:
        await _liaison().process(
            message="Status check.",
            overall_status="green",
            triage_items=[],
        )

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    assert isinstance(messages, list)
    assert any("Status check" in m.get("content", "") for m in messages)


@pytest.mark.unit
async def test_process_history_capped_at_window() -> None:
    """History is capped to the last _HISTORY_WINDOW messages."""
    long_history = [{"role": "user", "content": f"msg-{i}"} for i in range(20)]
    with _patch_liaison() as mock_client:
        await _liaison().process(
            message="Current.",
            overall_status="green",
            triage_items=[],
            history=long_history,
        )

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    # 1 (system) + 2 (context exchange) + _HISTORY_WINDOW (capped) + 1 (current)
    assert len(messages) == 1 + 2 + _HISTORY_WINDOW + 1


@pytest.mark.unit
async def test_process_history_maps_system_role_to_assistant() -> None:
    """'system' role in history maps to 'assistant' for the OpenAI-compatible messages API."""
    history = [{"role": "system", "content": "Prior liaison response."}]
    with _patch_liaison() as mock_client:
        await _liaison().process(
            message="Follow-up.",
            overall_status="green",
            triage_items=[],
            history=history,
        )

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    history_turns = [m for m in messages if "Prior liaison response" in m.get("content", "")]
    assert history_turns
    assert history_turns[0]["role"] == "assistant"
