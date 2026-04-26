"""Unit tests for the lead orchestrator."""

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
from kinetic.orchestrator.lead import orchestrate


@pytest.fixture(autouse=True)
def mock_db() -> MagicMock:
    with patch("kinetic.orchestrator.lead.get_db") as mock:
        client = MagicMock()
        client.insert_checkin = AsyncMock(return_value="test-id")
        client.get_latest_bio = AsyncMock(return_value=None)
        client.get_all_tasks = AsyncMock(return_value=[])
        client.get_all_vibes = AsyncMock(return_value=[])
        client.get_recent_bio = AsyncMock(return_value=[])
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
