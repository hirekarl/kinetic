"""Unit tests for liaison_context formatter functions."""

from __future__ import annotations

from datetime import datetime

import pytest

from kinetic.agents.liaison_context import format_behavioral_summary, format_bio_status
from kinetic.models.outputs import (
    BehavioralSummary,
    BioStatus,
    RecurringTask,
    RelationalDrift,
)


@pytest.mark.unit
def test_format_bio_status_includes_recommendations() -> None:
    """format_bio_status appends a Recommendations line when the list is non-empty."""
    bio = BioStatus(
        status="yellow",
        burnout_score=55.0,
        sleep_debt_hours=2.5,
        forecast="Moderate risk.",
        recommendations=["Target 8h sleep tonight.", "Hard stop at 11pm."],
    )
    output = format_bio_status(bio)

    assert "Recommendations:" in output
    assert "Target 8h sleep tonight." in output
    assert "Hard stop at 11pm." in output


@pytest.mark.unit
def test_format_bio_status_without_recommendations_omits_line() -> None:
    """format_bio_status has no Recommendations line when list is empty."""
    bio = BioStatus(
        status="green",
        burnout_score=20.0,
        sleep_debt_hours=0.5,
        forecast="Low burnout risk.",
    )
    output = format_bio_status(bio)

    assert "Recommendations:" not in output


@pytest.mark.unit
def test_format_behavioral_summary_includes_recurring_tasks() -> None:
    """format_behavioral_summary lists recurring tasks when the list is non-empty."""
    summary = BehavioralSummary(
        bio_trend=None,
        recurring_tasks=[
            RecurringTask(name="laundry", times_overdue=3, avg_days_overdue=4.5, priority="high")
        ],
        relational_drifts=[],
        days_analyzed=7,
        generated_at=datetime.now(),
    )
    output = format_behavioral_summary(summary)

    assert "laundry" in output
    assert "3x" in output


@pytest.mark.unit
def test_format_behavioral_summary_includes_relational_drifts() -> None:
    """format_behavioral_summary lists drifting contacts when relational_drifts is non-empty."""
    summary = BehavioralSummary(
        bio_trend=None,
        recurring_tasks=[],
        relational_drifts=[
            RelationalDrift(
                person="Marcus",
                contact_trend=1.5,
                avg_vibe_score=5.5,
                last_known_days_since_contact=9,
            )
        ],
        days_analyzed=7,
        generated_at=datetime.now(),
    )
    output = format_behavioral_summary(summary)

    assert "Marcus" in output
    assert "1.5" in output
