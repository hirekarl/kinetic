import pytest

from kinetic.models.inputs import (
    BioInput,
    CheckInPayload,
    LogisticsInput,
    LogisticsTask,
    RelationalInput,
    VibeCheck,
)
from kinetic.models.outputs import (
    BioStatus,
    LogisticsStatus,
    RelationalStatus,
    StatusLevel,
    SystemHealthPayload,
    TriageItem,
)


@pytest.fixture
def bio_input() -> BioInput:
    return BioInput(sleep_hours=6.5, nutrition_quality=7, energy_level=6)


@pytest.fixture
def logistics_input() -> LogisticsInput:
    return LogisticsInput(
        tasks=[
            LogisticsTask(name="laundry", days_overdue=2, priority="high"),
            LogisticsTask(name="groceries", days_overdue=0, priority="medium"),
        ]
    )


@pytest.fixture
def relational_input() -> RelationalInput:
    return RelationalInput(
        vibe_checks=[
            VibeCheck(person="Marcus", score=4, days_since_contact=11),
        ]
    )


@pytest.fixture
def full_checkin_payload(
    bio_input: BioInput,
    logistics_input: LogisticsInput,
    relational_input: RelationalInput,
) -> CheckInPayload:
    return CheckInPayload(
        bio=bio_input,
        logistics=logistics_input,
        relational=relational_input,
    )


@pytest.fixture
def empty_checkin_payload() -> CheckInPayload:
    return CheckInPayload()


@pytest.fixture
def sample_triage_item() -> TriageItem:
    return TriageItem(
        id="triage-001",
        priority=8,
        domain="logistics",
        description="Laundry overdue: 2 days",
        action="Schedule laundry pickup tonight (15 min)",
    )


@pytest.fixture
def sample_system_health(sample_triage_item: TriageItem) -> SystemHealthPayload:
    overall: StatusLevel = "yellow"
    return SystemHealthPayload(
        overall_status=overall,
        bio=BioStatus(
            status="yellow",
            burnout_score=62.0,
            forecast="Moderate risk. Hard stop recommended by 11pm.",
            sleep_debt_hours=3.5,
            recommendations=["Hard stop at 11pm", "Add 30-min wind-down"],
        ),
        logistics=LogisticsStatus(
            status="yellow",
            critical_tasks=["laundry"],
            outsourcing_suggestions=["Laundry pickup: ~$25, saves 2h weekend"],
            time_to_resolve_minutes=15,
        ),
        relational=RelationalStatus(
            status="red",
            connection_margin_score=28.0,
            at_risk_relationships=["Marcus"],
            interaction_sprints=["Text Marcus to schedule a call (30 sec)"],
        ),
        triage_items=[sample_triage_item],
    )
