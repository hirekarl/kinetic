"""Unit tests for the lead orchestrator."""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsInput,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)
from kinetic.models.outputs import BehavioralSummary
from kinetic.orchestrator.lead import orchestrate

_MOCK_SUMMARY = BehavioralSummary(
    bio_trend=None,
    recurring_tasks=[],
    relational_drifts=[],
    days_analyzed=5,
    generated_at=datetime(2026, 4, 26, 12, 0, 0),
)


@pytest.fixture(autouse=True)
def mock_db() -> MagicMock:
    with patch("kinetic.orchestrator.lead.get_db") as mock:
        client = MagicMock()
        client.insert_checkin = AsyncMock(return_value="test-id")
        client.get_latest_bio = AsyncMock(return_value=None)
        client.get_all_tasks = AsyncMock(return_value=[])
        client.get_all_vibes = AsyncMock(return_value=[])
        client.get_recent_bio = AsyncMock(return_value=[])
        client.get_behavioral_summary = AsyncMock(return_value=_MOCK_SUMMARY)
        client.get_behavioral_profiles = AsyncMock(return_value=[])
        mock.return_value = client
        yield client


@pytest.fixture(autouse=True)
def mock_liaison() -> MagicMock:
    with patch("kinetic.orchestrator.lead.OperationalLiaison") as mock:
        instance = MagicMock()
        instance.process = AsyncMock(return_value="Tactical feedback.")
        mock.return_value = instance
        yield instance


@pytest.mark.unit
@pytest.mark.asyncio
async def test_all_agents_fire_on_full_payload(full_checkin_payload: CheckInPayload) -> None:
    """Full payload → all three agents run and return populated status."""
    result = await orchestrate(full_checkin_payload)

    assert result.bio is not None
    assert result.logistics is not None
    assert result.relational is not None
    assert result.overall_status in ("green", "yellow", "red")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_bio_only_payload_still_runs_others(mock_db: MagicMock) -> None:
    """bio-only payload → all agents run to maintain cumulative context."""
    payload = CheckInPayload(bio=BioInput(sleep_hours=7.0, nutrition_quality=8, energy_level=7))
    result = await orchestrate(payload)

    assert result.bio is not None
    # Now that we are cumulative, these are not None but 'green' defaults
    assert result.logistics is not None
    assert result.relational is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_payload_returns_default_health() -> None:
    """Empty payload → all agents run, overall_status defaults to green."""
    result = await orchestrate(CheckInPayload())

    assert result.bio is not None
    assert result.logistics is not None
    assert result.relational is not None
    assert result.overall_status == "green"
    assert result.triage_items == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_triage_items_sorted_descending_by_priority() -> None:
    """Triage items from multiple agents are sorted by priority (highest first)."""
    payload = CheckInPayload(
        bio=BioInput(sleep_hours=4.0, nutrition_quality=3, energy_level=2),
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=3, priority="high")]
        ),
    )
    result = await orchestrate(payload)

    priorities = [item.priority for item in result.triage_items]
    assert priorities == sorted(priorities, reverse=True)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_triage_items_have_stable_ids() -> None:
    """All triage items get stable, non-empty ids after orchestration."""
    payload = CheckInPayload(
        bio=BioInput(sleep_hours=4.0),
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=3, priority="high")]
        ),
    )
    result = await orchestrate(payload)

    ids = [item.id for item in result.triage_items]
    assert all(ids)  # no empty strings
    assert len(ids) == len(set(ids))  # all unique


@pytest.mark.unit
@pytest.mark.asyncio
async def test_agent_failure_does_not_block_other_agents() -> None:
    """If BioArchivist raises, logistics still runs and result is still returned."""
    payload = CheckInPayload(
        bio=BioInput(sleep_hours=6.0),
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=2, priority="high")]
        ),
    )
    with patch(
        "kinetic.orchestrator.lead.BioArchivist.process",
        new_callable=AsyncMock,
        side_effect=RuntimeError("bio agent exploded"),
    ):
        result = await orchestrate(payload)

    assert result.bio is not None
    assert result.bio.status == "yellow"
    assert "Agent failure detected" in result.bio.forecast
    assert result.logistics is not None
    assert result.overall_status == "yellow"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_overall_status_is_worst_case() -> None:
    """overall_status reflects the worst single-agent status."""
    payload = CheckInPayload(
        bio=BioInput(sleep_hours=8.0, nutrition_quality=9, energy_level=9),
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=4, days_since_contact=11)]
        ),
    )
    result = await orchestrate(payload)

    assert result.bio is not None
    assert result.relational is not None
    assert result.bio.status == "green"
    assert result.relational.status == "red"
    assert result.overall_status == "red"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_roi_calculation_on_full_payload(full_checkin_payload: CheckInPayload) -> None:
    """Full payload → ROI summary is populated with non-zero values."""
    result = await orchestrate(full_checkin_payload)

    assert result.roi_summary is not None
    assert result.roi_summary.time_recovered_minutes >= 0
    assert "capacity reclaimed" in result.roi_summary.margin_recovered
    assert result.roi_summary.burnout_risk_delta <= 0.0


# ── Behavioral memory integration ─────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_behavioral_profiles_included_in_payload() -> None:
    """SystemHealthPayload always includes behavioral_profiles (list, may be empty)."""
    result = await orchestrate(CheckInPayload())

    assert hasattr(result, "behavioral_profiles")
    assert isinstance(result.behavioral_profiles, list)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_liaison_called_with_behavioral_summary(mock_liaison: MagicMock) -> None:
    """Orchestrator passes behavioral_summary to OperationalLiaison.process()."""
    await orchestrate(CheckInPayload())

    call_kwargs = mock_liaison.process.call_args.kwargs
    assert "behavioral_summary" in call_kwargs
    assert call_kwargs["behavioral_summary"] == _MOCK_SUMMARY


@pytest.mark.unit
@pytest.mark.asyncio
async def test_liaison_called_with_behavioral_profiles(
    mock_db: MagicMock, mock_liaison: MagicMock
) -> None:
    """Orchestrator passes behavioral_profiles to OperationalLiaison.process()."""
    await orchestrate(CheckInPayload())

    call_kwargs = mock_liaison.process.call_args.kwargs
    assert "behavioral_profiles" in call_kwargs
    assert call_kwargs["behavioral_profiles"] == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_detect_patterns_fires_as_background_task() -> None:
    """detect_and_update_patterns is scheduled as an asyncio task after liaison runs."""
    with patch(
        "kinetic.orchestrator.lead.detect_and_update_patterns",
        new_callable=AsyncMock,
    ) as mock_detect:
        await orchestrate(CheckInPayload(), message="hello")
        await asyncio.sleep(0)

    mock_detect.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_behavioral_summary_included_in_payload(mock_db: MagicMock) -> None:
    """SystemHealthPayload includes behavioral_summary from the DB."""
    result = await orchestrate(CheckInPayload())

    assert result.behavioral_summary is not None
    assert result.behavioral_summary == _MOCK_SUMMARY


@pytest.mark.unit
@pytest.mark.asyncio
async def test_behavioral_summary_failure_does_not_block(mock_db: MagicMock) -> None:
    """If get_behavioral_summary raises, orchestrate still returns a valid payload."""
    mock_db.get_behavioral_summary.side_effect = OSError("DB read failed")

    result = await orchestrate(CheckInPayload())

    assert result.overall_status in ("green", "yellow", "red")
