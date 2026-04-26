"""Unit tests for LogisticsFixer agent."""

import pytest

from kinetic.agents.logistics_fixer import LogisticsFixer
from kinetic.models.inputs import CheckInPayload, LogisticsInput, LogisticsTask


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_tasks_yields_green() -> None:
    """Empty task list → green status, no critical tasks."""
    payload = CheckInPayload(logistics=LogisticsInput(tasks=[]))
    result = await LogisticsFixer().process(payload)

    assert result.success is True
    assert result.status is not None
    assert result.status.status == "green"
    assert result.status.critical_tasks == []
    assert result.triage_items == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_zero_days_overdue_is_green() -> None:
    """Tasks with days_overdue=0 are not yet critical regardless of priority."""
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="groceries", days_overdue=0, priority="critical")]
        )
    )
    result = await LogisticsFixer().process(payload)

    assert result.status is not None
    assert result.status.status == "green"
    assert result.triage_items == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_yellow_task_yields_yellow_status() -> None:
    """laundry 2d overdue, high priority → criticality 6 → yellow."""
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=2, priority="high")]
        )
    )
    result = await LogisticsFixer().process(payload)

    assert result.status is not None
    assert result.status.status == "yellow"
    assert "laundry" in result.status.critical_tasks
    assert len(result.triage_items) >= 1
    assert all(item.domain == "logistics" for item in result.triage_items)
    assert all(item.priority == 5 for item in result.triage_items)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_red_task_yields_red_status() -> None:
    """laundry 3d overdue, high priority → criticality 9 → red; triage priority 8."""
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=3, priority="high")]
        )
    )
    result = await LogisticsFixer().process(payload)

    assert result.status is not None
    assert result.status.status == "red"
    assert "laundry" in result.status.critical_tasks
    assert len(result.triage_items) >= 1
    assert all(item.priority == 8 for item in result.triage_items)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_outsourcing_suggestion_for_known_task() -> None:
    """Known task names get an outsourcing suggestion."""
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=2, priority="high")]
        )
    )
    result = await LogisticsFixer().process(payload)

    assert result.status is not None
    assert len(result.status.outsourcing_suggestions) > 0
    assert any("laundry" in s.lower() for s in result.status.outsourcing_suggestions)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_logistics_input_returns_nominal_status() -> None:
    """Payload with logistics=None → success=True and nominal status."""
    payload = CheckInPayload()
    result = await LogisticsFixer().process(payload)

    assert result.success is True
    assert result.status is not None
    assert result.status.status == "green"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_time_to_resolve_non_zero_for_critical_tasks() -> None:
    """time_to_resolve_minutes is positive when there are non-green tasks."""
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=2, priority="high")]
        )
    )
    result = await LogisticsFixer().process(payload)

    assert result.status is not None
    assert result.status.time_to_resolve_minutes > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_triage_items_carry_source_id_equal_to_task_name() -> None:
    """All logistics triage items must have source_id set to the originating task name."""
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[
                LogisticsTask(name="laundry", days_overdue=3, priority="high"),
                LogisticsTask(name="groceries", days_overdue=2, priority="medium"),
            ]
        )
    )
    result = await LogisticsFixer().process(payload)

    assert len(result.triage_items) >= 1
    for item in result.triage_items:
        assert item.source_id is not None, (
            f"source_id must not be None for logistics item {item.description}"
        )
        assert item.source_id in {"laundry", "groceries"}
