"""Unit tests for the lead orchestrator."""

from unittest.mock import AsyncMock, patch

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
async def test_bio_only_payload_skips_other_agents() -> None:
    """bio-only payload → only bio runs; logistics and relational are None."""
    payload = CheckInPayload(bio=BioInput(sleep_hours=7.0, nutrition_quality=8, energy_level=7))
    result = await orchestrate(payload)

    assert result.bio is not None
    assert result.logistics is None
    assert result.relational is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_payload_returns_green_no_agents() -> None:
    """Empty payload → no agents run, overall_status defaults to green."""
    result = await orchestrate(CheckInPayload())

    assert result.bio is None
    assert result.logistics is None
    assert result.relational is None
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

    assert result.bio is None
    assert result.logistics is not None
    assert result.overall_status in ("green", "yellow", "red")


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
