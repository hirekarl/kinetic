"""Bootstrap smoke tests — verifies Pydantic models instantiate and validate correctly."""

import pytest
from pydantic import ValidationError

from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)
from kinetic.models.outputs import SystemHealthPayload, TriageItem


@pytest.mark.unit
def test_checkin_payload_all_none_is_valid() -> None:
    payload = CheckInPayload()
    assert payload.bio is None
    assert payload.logistics is None
    assert payload.relational is None


@pytest.mark.unit
def test_bio_input_validates_sleep_range() -> None:
    bio = BioInput(sleep_hours=7.5, nutrition_quality=8, energy_level=7)
    assert bio.sleep_hours == 7.5
    with pytest.raises(ValidationError):
        BioInput(sleep_hours=25)  # >24 hours invalid


@pytest.mark.unit
def test_logistics_task_days_overdue_defaults_to_zero() -> None:
    task = LogisticsTask(name="laundry", priority="high")
    assert task.days_overdue == 0


@pytest.mark.unit
def test_vibe_check_score_range_enforced() -> None:
    vc = VibeCheck(person="Marcus", score=4, days_since_contact=11)
    assert vc.score == 4
    with pytest.raises(ValidationError):
        VibeCheck(person="Marcus", score=11, days_since_contact=0)  # >10 invalid


@pytest.mark.unit
def test_system_health_payload_triage_items_default_empty(
    sample_system_health: SystemHealthPayload,
) -> None:
    assert isinstance(sample_system_health.triage_items, list)
    assert len(sample_system_health.triage_items) == 1
    item: TriageItem = sample_system_health.triage_items[0]
    assert item.domain == "logistics"


@pytest.mark.unit
def test_full_checkin_payload_roundtrip(full_checkin_payload: CheckInPayload) -> None:
    data = full_checkin_payload.model_dump()
    restored = CheckInPayload.model_validate(data)
    assert restored.bio is not None
    assert restored.logistics is not None
    assert restored.relational is not None


@pytest.mark.unit
def test_checkin_payload_partial_bio_only() -> None:
    payload = CheckInPayload(bio=BioInput(sleep_hours=5.0))
    assert payload.bio is not None
    assert payload.logistics is None
    assert payload.relational is None


@pytest.mark.unit
def test_checkin_payload_partial_relational_only() -> None:
    payload = CheckInPayload(
        relational=RelationalInput(
            vibe_checks=[VibeCheck(person="Alex", score=7, days_since_contact=3)]
        )
    )
    assert payload.bio is None
    assert payload.logistics is None
    assert payload.relational is not None
    assert payload.relational.vibe_checks[0].person == "Alex"
