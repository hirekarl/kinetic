"""Unit tests for RelationalDiplomat agent."""

import pytest

from kinetic.agents.relational_diplomat import RelationalDiplomat
from kinetic.models.inputs import CheckInPayload, RelationalInput, VibeCheck


@pytest.mark.unit
@pytest.mark.asyncio
async def test_healthy_relationships_yield_green() -> None:
    """High score, recent contact → green status, no at-risk."""
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Alex", score=8, days_since_contact=3)]
        )
    )
    result = await RelationalDiplomat().process(payload)

    assert result.success is True
    assert result.status is not None
    assert result.status.status == "green"
    assert result.status.at_risk_relationships == []
    assert result.triage_items == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_low_score_at_risk_yields_red() -> None:
    """Score < 5 is a hard at-risk signal → red status; triage priority 8."""
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=4, days_since_contact=11)]
        )
    )
    result = await RelationalDiplomat().process(payload)

    assert result.status is not None
    assert result.status.status == "red"
    assert "Marcus" in result.status.at_risk_relationships
    assert len(result.triage_items) >= 1
    assert all(item.priority == 8 for item in result.triage_items)
    assert all(item.domain == "relational" for item in result.triage_items)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stale_contact_only_yields_yellow() -> None:
    """Good score but days > 7 → yellow; triage priority 5."""
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Jordan", score=7, days_since_contact=14)]
        )
    )
    result = await RelationalDiplomat().process(payload)

    assert result.status is not None
    assert result.status.status == "yellow"
    assert "Jordan" in result.status.at_risk_relationships
    assert len(result.triage_items) >= 1
    assert all(item.priority == 5 for item in result.triage_items)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_vibe_checks_yields_green() -> None:
    """No vibe checks → green, perfect margin."""
    payload = CheckInPayload(relational=RelationalInput(vibe_checks=[]))
    result = await RelationalDiplomat().process(payload)

    assert result.status is not None
    assert result.status.status == "green"
    assert result.status.connection_margin_score == pytest.approx(100.0)
    assert result.triage_items == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_relational_input_returns_nominal_status() -> None:
    """Payload with relational=None → success=True, nominal status."""
    payload = CheckInPayload()
    result = await RelationalDiplomat().process(payload)

    assert result.success is True
    assert result.status is not None
    assert result.status.status == "green"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_connection_margin_decays_with_stale_contact() -> None:
    """Connection margin is lower when contact is stale vs. recent."""
    fresh_payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Alex", score=8, days_since_contact=2)]
        )
    )
    stale_payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Alex", score=8, days_since_contact=20)]
        )
    )
    fresh_result = await RelationalDiplomat().process(fresh_payload)
    stale_result = await RelationalDiplomat().process(stale_payload)

    assert fresh_result.status is not None
    assert stale_result.status is not None
    assert fresh_result.status.connection_margin_score > stale_result.status.connection_margin_score


@pytest.mark.unit
@pytest.mark.asyncio
async def test_interaction_sprints_generated_for_at_risk() -> None:
    """At-risk relationships get interaction sprint suggestions."""
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=4, days_since_contact=11)]
        )
    )
    result = await RelationalDiplomat().process(payload)

    assert result.status is not None
    assert len(result.status.interaction_sprints) > 0
    assert any("Marcus" in sprint for sprint in result.status.interaction_sprints)
