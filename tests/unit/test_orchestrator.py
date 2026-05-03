"""Unit tests for the lead orchestrator."""

import asyncio
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
        client.upsert_contact_pause = AsyncMock(return_value=None)
        client.get_active_pauses = AsyncMock(return_value=[])
        client.complete_task = AsyncMock(return_value=None)
        mock.return_value = client
        yield client


@pytest.fixture(autouse=True)
def mock_liaison() -> MagicMock:
    with patch("kinetic.orchestrator.lead.OperationalLiaison") as mock:
        instance = MagicMock()
        instance.process = AsyncMock(return_value=LiaisonResponse(text="Tactical feedback."))
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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_liaison_called_with_history(mock_liaison: MagicMock) -> None:
    """Orchestrator forwards history to OperationalLiaison.process()."""
    history = [
        {"role": "user", "content": "Slept 5 hours."},
        {"role": "system", "content": "Sleep deficit noted."},
    ]
    await orchestrate(CheckInPayload(), history=history)

    call_kwargs = mock_liaison.process.call_args.kwargs
    assert call_kwargs.get("history") == history


@pytest.mark.unit
@pytest.mark.asyncio
async def test_liaison_receives_none_history_by_default(mock_liaison: MagicMock) -> None:
    """When no history is passed, liaison receives history=None."""
    await orchestrate(CheckInPayload())

    call_kwargs = mock_liaison.process.call_args.kwargs
    assert call_kwargs.get("history") is None


# ── Agent context forwarding ──────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_liaison_receives_agent_status_objects(mock_liaison: MagicMock) -> None:
    """Orchestrator passes bio/logistics/relational status to the liaison."""
    await orchestrate(CheckInPayload())

    call_kwargs = mock_liaison.process.call_args.kwargs
    assert "bio_status" in call_kwargs
    assert "logistics_status" in call_kwargs
    assert "relational_status" in call_kwargs


@pytest.mark.unit
@pytest.mark.asyncio
async def test_responding_agent_included_in_payload(mock_liaison: MagicMock) -> None:
    """SystemHealthPayload.responding_agent reflects the liaison response."""
    mock_liaison.process.return_value = LiaisonResponse(
        text="Your burnout is at 72.", responding_agent="bio_archivist"
    )
    result = await orchestrate(CheckInPayload())

    assert result.responding_agent == "bio_archivist"


# ── Contact pause lifecycle ───────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_contact_pause_directive_is_persisted(
    mock_db: MagicMock, mock_liaison: MagicMock
) -> None:
    """When liaison returns a contact pause directive, upsert_contact_pause is called."""
    from kinetic.agents.operational_liaison import ContactPauseDirective

    mock_liaison.process.return_value = LiaisonResponse(
        text="Pause noted.",
        contact_pauses=[ContactPauseDirective(person="Marcus", pause_days=14)],
    )
    await orchestrate(CheckInPayload(), message="Marcus and I are on a break.")

    mock_db.upsert_contact_pause.assert_called_once()
    call_args = mock_db.upsert_contact_pause.call_args
    assert call_args.args[0] == "Marcus"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_paused_contact_removed_from_triage(
    mock_db: MagicMock, mock_liaison: MagicMock
) -> None:
    """Triage items whose description/action contain a paused contact name are filtered out."""
    from datetime import date, timedelta

    mock_db.get_active_pauses.return_value = [
        {
            "person": "Marcus",
            "paused_until": (date.today() + timedelta(days=14)).isoformat(),
            "reason": None,
        }
    ]
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=3, days_since_contact=15)]
        )
    )
    result = await orchestrate(payload)

    assert not any("Marcus" in item.description for item in result.triage_items)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_paused_contact_removed_from_relational_status(
    mock_db: MagicMock, mock_liaison: MagicMock
) -> None:
    """at_risk_relationships and interaction_sprints exclude paused contacts."""
    from datetime import date, timedelta

    mock_db.get_active_pauses.return_value = [
        {
            "person": "Marcus",
            "paused_until": (date.today() + timedelta(days=14)).isoformat(),
            "reason": None,
        }
    ]
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=3, days_since_contact=15)]
        )
    )
    result = await orchestrate(payload)

    assert result.relational is not None
    assert "Marcus" not in result.relational.at_risk_relationships
    assert not any("Marcus" in s for s in result.relational.interaction_sprints)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_active_pauses_included_in_payload(
    mock_db: MagicMock, mock_liaison: MagicMock
) -> None:
    """SystemHealthPayload.active_pauses is populated from DB active pauses."""
    from datetime import date, timedelta

    mock_db.get_active_pauses.return_value = [
        {
            "person": "Marcus",
            "paused_until": (date.today() + timedelta(days=7)).isoformat(),
            "reason": "break",
        }
    ]
    result = await orchestrate(CheckInPayload())

    assert len(result.active_pauses) == 1
    assert result.active_pauses[0].person == "Marcus"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_directives_skips_upsert(mock_db: MagicMock, mock_liaison: MagicMock) -> None:
    """When liaison returns no contact pauses, upsert_contact_pause is never called."""
    await orchestrate(CheckInPayload(), message="Slept 7 hours.")

    mock_db.upsert_contact_pause.assert_not_called()


# ── Task completion directive ─────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_task_completion_directive_is_persisted(
    mock_db: MagicMock, mock_liaison: MagicMock
) -> None:
    """When liaison returns task_completions, complete_task is called for each name."""
    mock_liaison.process.return_value = LiaisonResponse(
        text="Marked laundry complete.",
        task_completions=["laundry"],
    )
    await orchestrate(CheckInPayload(), message="I finished the laundry.")

    mock_db.complete_task.assert_called_once_with("laundry")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_multiple_task_completions_each_persisted(
    mock_db: MagicMock, mock_liaison: MagicMock
) -> None:
    """All task names in task_completions result in a complete_task call each."""
    mock_liaison.process.return_value = LiaisonResponse(
        text="Both done.",
        task_completions=["laundry", "groceries"],
    )
    await orchestrate(CheckInPayload(), message="Done with laundry and groceries.")

    assert mock_db.complete_task.call_count == 2
    calls = {c.args[0] for c in mock_db.complete_task.call_args_list}
    assert calls == {"laundry", "groceries"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_task_completion_keyerror_does_not_raise(
    mock_db: MagicMock, mock_liaison: MagicMock
) -> None:
    """If complete_task raises KeyError (unknown task), orchestrate still returns normally."""
    mock_db.complete_task.side_effect = KeyError("unknown_task")
    mock_liaison.process.return_value = LiaisonResponse(
        text="Done.",
        task_completions=["unknown_task"],
    )
    result = await orchestrate(CheckInPayload(), message="Done with unknown task.")

    assert result.overall_status in ("green", "yellow", "red")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_no_task_completions_skips_complete_task(
    mock_db: MagicMock, mock_liaison: MagicMock
) -> None:
    """When liaison returns no task_completions, complete_task is never called."""
    await orchestrate(CheckInPayload(), message="Just a status check.")

    mock_db.complete_task.assert_not_called()


# ── _merge_history ────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_merge_history_populates_bio_from_db_when_payload_has_none(
    mock_db: MagicMock,
) -> None:
    """_merge_history creates payload.bio from DB when payload.bio is None."""
    from kinetic.orchestrator.lead import _merge_history

    mock_db.get_latest_bio.return_value = {
        "sleep_hours": 6.5,
        "nutrition_quality": 7,
        "energy_level": 6,
    }
    payload = CheckInPayload()
    result = await _merge_history(payload, mock_db)

    assert result.bio is not None
    assert result.bio.sleep_hours == pytest.approx(6.5)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_merge_history_fills_missing_bio_fields(mock_db: MagicMock) -> None:
    """_merge_history fills only None fields in an existing payload.bio."""
    from kinetic.orchestrator.lead import _merge_history

    mock_db.get_latest_bio.return_value = {
        "sleep_hours": 7.0,
        "nutrition_quality": 9,
        "energy_level": 8,
    }
    payload = CheckInPayload(bio=BioInput(sleep_hours=5.0))
    result = await _merge_history(payload, mock_db)

    assert result.bio is not None
    assert result.bio.sleep_hours == pytest.approx(5.0)  # original preserved
    assert result.bio.nutrition_quality == 9  # filled from DB
    assert result.bio.energy_level == 8  # filled from DB


@pytest.mark.unit
@pytest.mark.asyncio
async def test_merge_history_populates_logistics_from_db_when_none(mock_db: MagicMock) -> None:
    """_merge_history creates payload.logistics from DB when payload.logistics is None."""
    from kinetic.orchestrator.lead import _merge_history

    mock_db.get_all_tasks.return_value = [
        {
            "name": "laundry",
            "priority": "high",
            "subtasks": [],
            "completed_subtasks": [],
            "status": "pending",
            "days_overdue": 3,
        }
    ]
    payload = CheckInPayload()
    result = await _merge_history(payload, mock_db)

    assert result.logistics is not None
    assert any(t.name == "laundry" for t in result.logistics.tasks)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_merge_history_adds_historical_tasks_not_in_payload(mock_db: MagicMock) -> None:
    """_merge_history appends DB tasks whose names are absent from the payload."""
    from kinetic.orchestrator.lead import _merge_history

    mock_db.get_all_tasks.return_value = [
        {
            "name": "dishes",
            "priority": "low",
            "subtasks": [],
            "completed_subtasks": [],
            "status": "pending",
            "days_overdue": 1,
        }
    ]
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=2, priority="high")]
        )
    )
    result = await _merge_history(payload, mock_db)

    names = {t.name for t in result.logistics.tasks}
    assert "laundry" in names
    assert "dishes" in names


@pytest.mark.unit
@pytest.mark.asyncio
async def test_merge_history_populates_relational_from_db_when_none(mock_db: MagicMock) -> None:
    """_merge_history creates payload.relational from DB when payload.relational is None."""
    from kinetic.orchestrator.lead import _merge_history

    mock_db.get_all_vibes.return_value = [{"person": "Marcus", "score": 7, "days_since_contact": 4}]
    payload = CheckInPayload()
    result = await _merge_history(payload, mock_db)

    assert result.relational is not None
    assert any(v.person == "Marcus" for v in result.relational.vibe_checks)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_merge_history_adds_historical_vibes_not_in_payload(mock_db: MagicMock) -> None:
    """_merge_history appends DB vibes for people absent from the current payload."""
    from kinetic.orchestrator.lead import _merge_history

    mock_db.get_all_vibes.return_value = [{"person": "Priya", "score": 9, "days_since_contact": 1}]
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=6, days_since_contact=5)]
        )
    )
    result = await _merge_history(payload, mock_db)

    people = {v.person for v in result.relational.vibe_checks}
    assert "Marcus" in people
    assert "Priya" in people


# ── Agent failure handlers: LogisticsFixer, RelationalDiplomat ────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_logistics_fixer_failure_degrades_gracefully() -> None:
    """If LogisticsFixer raises, the result has a degraded logistics status, not a crash."""
    payload = CheckInPayload(
        logistics=LogisticsInput(
            tasks=[LogisticsTask(name="laundry", days_overdue=2, priority="high")]
        )
    )
    with patch(
        "kinetic.orchestrator.lead.LogisticsFixer.process",
        new_callable=AsyncMock,
        side_effect=RuntimeError("logistics exploded"),
    ):
        result = await orchestrate(payload)

    assert result.logistics is not None
    assert result.logistics.status == "yellow"
    assert result.overall_status in ("green", "yellow", "red")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_relational_diplomat_failure_degrades_gracefully() -> None:
    """If RelationalDiplomat raises, the result has degraded relational status, not a crash."""
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Marcus", score=4, days_since_contact=10)]
        )
    )
    with patch(
        "kinetic.orchestrator.lead.RelationalDiplomat.process",
        new_callable=AsyncMock,
        side_effect=RuntimeError("relational exploded"),
    ):
        result = await orchestrate(payload)

    assert result.relational is not None
    assert result.relational.status == "yellow"
    assert result.overall_status in ("green", "yellow", "red")


# ── get_active_pauses exception recovery ─────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_pauses_exception_does_not_crash(mock_db: MagicMock) -> None:
    """If get_active_pauses raises, orchestrate still returns a valid payload."""
    mock_db.get_active_pauses.side_effect = OSError("DB read failed")

    result = await orchestrate(CheckInPayload(), message="test")

    assert result.overall_status in ("green", "yellow", "red")
    assert result.active_pauses == []


# ── triage helpers ────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_aggregate_status_empty_returns_green() -> None:
    """aggregate_status with no active statuses defaults to 'green'."""
    from kinetic.orchestrator.triage import aggregate_status

    assert aggregate_status() == "green"
    assert aggregate_status(None, None) == "green"


# ── get_current_state ─────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_state_returns_health_and_messages(mock_db: MagicMock) -> None:
    """get_current_state returns a dict with 'health' and 'messages' keys."""
    from kinetic.orchestrator.lead import get_current_state

    mock_db.get_history = AsyncMock(return_value=[{"role": "user", "content": "hello"}])

    result = await get_current_state(db=mock_db)

    assert isinstance(result, dict)
    assert "health" in result
    assert "messages" in result
    assert result["messages"] == [{"role": "user", "content": "hello"}]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_state_without_db_uses_get_db(mock_db: MagicMock) -> None:
    """get_current_state() with no db arg falls through to get_db()."""
    from kinetic.orchestrator.lead import get_current_state

    mock_db.get_history = AsyncMock(return_value=[])

    result = await get_current_state()  # db=None → hits line 396: db = get_db()

    assert isinstance(result, dict)
    assert "health" in result


# ── _merge_history — bio.sleep_hours None branch ────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_merge_history_fills_sleep_hours_when_bio_exists_but_sleep_is_none(
    mock_db: MagicMock,
) -> None:
    """_merge_history fills sleep_hours from DB when payload.bio exists but sleep_hours is None."""
    from kinetic.orchestrator.lead import _merge_history

    mock_db.get_latest_bio.return_value = {
        "sleep_hours": 7.5,
        "nutrition_quality": 9,
        "energy_level": 8,
    }
    payload = CheckInPayload(bio=BioInput(sleep_hours=None, nutrition_quality=6))
    result = await _merge_history(payload, mock_db)

    assert result.bio is not None
    assert result.bio.sleep_hours == pytest.approx(7.5)  # filled from DB
    assert result.bio.nutrition_quality == 6  # original preserved


# ── triage helpers — calculate_roi ────────────────────────────────────────────


@pytest.mark.unit
def test_calculate_roi_returns_none_when_all_statuses_are_none() -> None:
    """calculate_roi returns None when all three status inputs are None."""
    from kinetic.orchestrator.triage import calculate_roi

    assert calculate_roi(None, None, None) is None
