"""Bootstrap smoke tests — verifies Pydantic models instantiate and validate correctly."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)
from kinetic.models.outputs import (
    BehavioralProfile,
    BehavioralSummary,
    BioTrend,
    SystemHealthPayload,
    TriageItem,
)


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


@pytest.mark.unit
def test_behavioral_profile_requires_all_fields() -> None:
    now = datetime.now()
    with pytest.raises(ValidationError):
        BehavioralProfile(  # type: ignore[call-arg]
            profile_key="sleep_pattern",
            # insight missing
            evidence={},
            first_observed=now,
            last_updated=now,
            observation_count=1,
        )


@pytest.mark.unit
def test_behavioral_summary_json_roundtrip() -> None:
    now = datetime.now()
    summary = BehavioralSummary(
        bio_trend=BioTrend(
            avg_sleep_hours=6.5,
            sleep_slope=-0.25,
            avg_nutrition=7.0,
            avg_energy=6.0,
            worst_sleep_day="2026-04-23",
            days_analyzed=7,
        ),
        recurring_tasks=[],
        relational_drifts=[],
        days_analyzed=7,
        generated_at=now,
    )
    restored = BehavioralSummary.model_validate(summary.model_dump())
    assert restored.bio_trend is not None
    assert restored.bio_trend.sleep_slope == pytest.approx(-0.25)
    assert restored.bio_trend.worst_sleep_day == "2026-04-23"
    assert restored.days_analyzed == 7


@pytest.mark.unit
def test_bio_trend_default_sleep_series() -> None:
    trend = BioTrend(
        avg_sleep_hours=7.0,
        sleep_slope=-0.1,
        avg_nutrition=7.0,
        avg_energy=7.0,
        days_analyzed=3,
    )
    assert trend.sleep_series == []


@pytest.mark.unit
def test_bio_trend_sleep_series_stored() -> None:
    trend = BioTrend(
        avg_sleep_hours=6.5,
        sleep_slope=-0.25,
        avg_nutrition=7.0,
        avg_energy=6.0,
        days_analyzed=3,
        sleep_series=[7.0, 6.5, 6.0],
    )
    assert trend.sleep_series == [7.0, 6.5, 6.0]


@pytest.mark.unit
def test_system_health_payload_behavioral_summary_defaults_none() -> None:
    payload = SystemHealthPayload(overall_status="green")
    assert payload.behavioral_summary is None


@pytest.mark.unit
def test_system_health_payload_accepts_behavioral_summary() -> None:
    now = datetime.now()
    summary = BehavioralSummary(
        bio_trend=BioTrend(
            avg_sleep_hours=6.5,
            sleep_slope=-0.25,
            avg_nutrition=7.0,
            avg_energy=6.0,
            days_analyzed=3,
            sleep_series=[7.0, 6.5, 6.0],
        ),
        days_analyzed=3,
        generated_at=now,
    )
    payload = SystemHealthPayload(overall_status="green", behavioral_summary=summary)
    assert payload.behavioral_summary is not None
    assert payload.behavioral_summary.bio_trend is not None
    assert payload.behavioral_summary.bio_trend.sleep_series == [7.0, 6.5, 6.0]


@pytest.mark.unit
def test_system_health_payload_accepts_behavioral_profiles() -> None:
    now = datetime.now()
    profile = BehavioralProfile(
        profile_key="work_boundary_violation",
        insight="Frequently works past 10pm.",
        evidence={"late_sessions": 4},
        first_observed=now,
        last_updated=now,
        observation_count=3,
    )
    payload = SystemHealthPayload(
        overall_status="yellow",
        behavioral_profiles=[profile],
    )
    assert len(payload.behavioral_profiles) == 1
    assert payload.behavioral_profiles[0].profile_key == "work_boundary_violation"
