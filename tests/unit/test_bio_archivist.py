"""Unit tests for BioArchivist agent."""

import pytest

from kinetic.agents.bio_archivist import BioArchivist
from kinetic.models.inputs import BioInput, CheckInPayload


@pytest.mark.unit
@pytest.mark.asyncio
async def test_full_input_yields_green() -> None:
    """6.5h sleep, nutrition 7, energy 6 → burnout ~38 → green."""
    payload = CheckInPayload(bio=BioInput(sleep_hours=6.5, nutrition_quality=7, energy_level=6))
    result = await BioArchivist().process(payload)

    assert result.success is True
    assert result.status is not None
    assert result.status.status == "green"
    assert 0 <= result.status.burnout_score < 40
    assert result.status.sleep_debt_hours == pytest.approx(1.5)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_sleep_only_yields_yellow() -> None:
    """5.5h sleep, no other data → burnout 62.5 → yellow; sleep debt 2.5h."""
    payload = CheckInPayload(bio=BioInput(sleep_hours=5.5))
    result = await BioArchivist().process(payload)

    assert result.success is True
    assert result.status is not None
    assert result.status.status == "yellow"
    assert 40 <= result.status.burnout_score < 70
    assert result.status.sleep_debt_hours == pytest.approx(2.5)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_high_stress_yields_red() -> None:
    """4h sleep, nutrition 3, energy 2 → burnout ~90 → red; triage item priority 9."""
    payload = CheckInPayload(bio=BioInput(sleep_hours=4.0, nutrition_quality=3, energy_level=2))
    result = await BioArchivist().process(payload)

    assert result.success is True
    assert result.status is not None
    assert result.status.status == "red"
    assert result.status.burnout_score >= 70
    assert len(result.triage_items) > 0
    assert all(item.priority == 9 for item in result.triage_items)
    assert all(item.domain == "bio" for item in result.triage_items)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_bio_input_returns_failure() -> None:
    """Payload with bio=None → success=False, no status."""
    payload = CheckInPayload()
    result = await BioArchivist().process(payload)

    assert result.success is False
    assert result.status is None
    assert result.error_message is not None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_yellow_status_generates_triage_item() -> None:
    """Yellow status yields a bio triage item with priority 6."""
    payload = CheckInPayload(bio=BioInput(sleep_hours=5.5))
    result = await BioArchivist().process(payload)

    assert result.status is not None
    assert result.status.status == "yellow"
    assert len(result.triage_items) >= 1
    assert all(item.domain == "bio" for item in result.triage_items)
    assert all(item.priority == 6 for item in result.triage_items)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_green_status_has_no_triage_items() -> None:
    """Green burnout produces no triage items."""
    payload = CheckInPayload(bio=BioInput(sleep_hours=8.0, nutrition_quality=9, energy_level=9))
    result = await BioArchivist().process(payload)

    assert result.status is not None
    assert result.status.status == "green"
    assert result.triage_items == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_historical_sleep_debt_increases_burnout() -> None:
    """Historical sleep debt should be reflected in today's score and debt."""
    payload = CheckInPayload(bio=BioInput(sleep_hours=7.0, nutrition_quality=9, energy_level=9))
    # No history
    res1 = await BioArchivist().process(payload)

    # With history: 4h sleep yesterday (4h deficit)
    history = {"bio": [{"sleep_hours": 4.0}]}
    res2 = await BioArchivist().process(payload, history=history)

    # 1h debt today + 4h debt yesterday = 5h total debt
    assert res2.status is not None
    assert res1.status is not None
    assert res2.status.sleep_debt_hours == pytest.approx(5.0)
    # 5h debt < 10h threshold, so score might not increase yet, but let's check debt
    assert res2.status.sleep_debt_hours > res1.status.sleep_debt_hours

    # With massive history: 15h total debt
    history_massive = {"bio": [{"sleep_hours": 4.0}, {"sleep_hours": 4.0}, {"sleep_hours": 4.0}]}
    res3 = await BioArchivist().process(payload, history=history_massive)
    # 1h + 4*3 = 13h debt
    assert res3.status is not None
    assert res3.status.sleep_debt_hours == pytest.approx(13.0)
    # debt > 10 → score should increase
    assert res3.status.burnout_score > res1.status.burnout_score
