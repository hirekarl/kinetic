"""Unit tests for Sprint 10 streaming — LiaisonMetadata, stream_text, extract_metadata, orchestrate_stream."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kinetic.agents.operational_liaison import (
    ContactPauseDirective,
    LiaisonMetadata,
    OperationalLiaison,
)
from kinetic.models.inputs import CheckInPayload
from kinetic.orchestrator.lead import orchestrate_stream

# ── LiaisonMetadata model ─────────────────────────────────────────────────────


@pytest.mark.unit
def test_liaison_metadata_defaults() -> None:
    """LiaisonMetadata has safe defaults."""
    m = LiaisonMetadata()
    assert m.responding_agent == "liaison"
    assert m.contact_pauses == []
    assert m.task_completions == []


@pytest.mark.unit
def test_liaison_metadata_with_values() -> None:
    """LiaisonMetadata stores provided values."""
    m = LiaisonMetadata(
        responding_agent="bio_archivist",
        contact_pauses=[ContactPauseDirective(person="Alice", pause_days=7)],
        task_completions=["laundry"],
    )
    assert m.responding_agent == "bio_archivist"
    assert len(m.contact_pauses) == 1
    assert m.task_completions == ["laundry"]


# ── stream_text() ─────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stream_text_yields_text_chunks() -> None:
    """stream_text() yields string chunks from the raw genai client."""

    async def fake_stream(*args: object, **kwargs: object) -> AsyncGenerator[MagicMock, None]:
        for text in ["Hello", " world", "!"]:
            chunk = MagicMock()
            chunk.text = text
            yield chunk

    liaison = OperationalLiaison(api_key="test-key")
    with (
        patch("kinetic.agents.operational_liaison.genai.Client"),
        patch("kinetic.agents.operational_liaison.instructor.from_genai"),
    ):
        liaison._raw_client = MagicMock()
        liaison._raw_client.aio.models.generate_content_stream = AsyncMock(
            return_value=fake_stream()
        )
        chunks: list[str] = []
        async for chunk in liaison.stream_text(
            message="Tired.",
            overall_status="yellow",
            triage_items=[],
        ):
            chunks.append(chunk)

    assert chunks == ["Hello", " world", "!"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_stream_text_skips_empty_chunks() -> None:
    """stream_text() skips chunks where chunk.text is falsy."""

    async def fake_stream(*args: object, **kwargs: object) -> AsyncGenerator[MagicMock, None]:
        for text in ["Hello", "", None, " world"]:
            chunk = MagicMock()
            chunk.text = text
            yield chunk

    liaison = OperationalLiaison(api_key="test-key")
    with (
        patch("kinetic.agents.operational_liaison.genai.Client"),
        patch("kinetic.agents.operational_liaison.instructor.from_genai"),
    ):
        liaison._raw_client = MagicMock()
        liaison._raw_client.aio.models.generate_content_stream = AsyncMock(
            return_value=fake_stream()
        )
        chunks: list[str] = []
        async for chunk in liaison.stream_text(
            message="Check-in.",
            overall_status="green",
            triage_items=[],
        ):
            chunks.append(chunk)

    assert chunks == ["Hello", " world"]


# ── extract_metadata() ────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_metadata_returns_defaults_when_no_keywords() -> None:
    """extract_metadata() returns defaults without calling Instructor when no keywords."""
    with (
        patch("kinetic.agents.operational_liaison.genai.Client"),
        patch("kinetic.agents.operational_liaison.instructor.from_genai") as mock_from_genai,
    ):
        mock_instructor_client = MagicMock()
        mock_from_genai.return_value = mock_instructor_client
        liaison = OperationalLiaison(api_key="test-key")

        result = await liaison.extract_metadata(
            streamed_text="Your sleep is the priority tonight.",
            message="Slept 5 hours, ate okay.",
        )

    assert isinstance(result, LiaisonMetadata)
    assert result.responding_agent == "liaison"
    assert result.contact_pauses == []
    assert result.task_completions == []
    mock_instructor_client.chat.completions.create.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_metadata_calls_instructor_for_pause_keyword() -> None:
    """extract_metadata() calls Instructor when 'pause' appears in the message."""
    expected = LiaisonMetadata(
        contact_pauses=[ContactPauseDirective(person="Marcus", pause_days=14)]
    )
    with (
        patch("kinetic.agents.operational_liaison.genai.Client"),
        patch("kinetic.agents.operational_liaison.instructor.from_genai") as mock_from_genai,
    ):
        mock_instructor_client = MagicMock()
        mock_instructor_client.chat.completions.create.return_value = expected
        mock_from_genai.return_value = mock_instructor_client
        liaison = OperationalLiaison(api_key="test-key")

        result = await liaison.extract_metadata(
            streamed_text="Contact pause noted for Marcus.",
            message="Marcus and I are on a pause for 2 weeks.",
        )

    assert len(result.contact_pauses) == 1
    assert result.contact_pauses[0].person == "Marcus"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_metadata_calls_instructor_for_completed_keyword() -> None:
    """extract_metadata() calls Instructor when 'completed' appears in the message."""
    expected = LiaisonMetadata(task_completions=["laundry"])
    with (
        patch("kinetic.agents.operational_liaison.genai.Client"),
        patch("kinetic.agents.operational_liaison.instructor.from_genai") as mock_from_genai,
    ):
        mock_instructor_client = MagicMock()
        mock_instructor_client.chat.completions.create.return_value = expected
        mock_from_genai.return_value = mock_instructor_client
        liaison = OperationalLiaison(api_key="test-key")

        result = await liaison.extract_metadata(
            streamed_text="Laundry marked done.",
            message="I completed the laundry.",
        )

    assert result.task_completions == ["laundry"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_extract_metadata_returns_defaults_on_instructor_failure() -> None:
    """extract_metadata() returns LiaisonMetadata defaults if Instructor raises."""
    with (
        patch("kinetic.agents.operational_liaison.genai.Client"),
        patch("kinetic.agents.operational_liaison.instructor.from_genai") as mock_from_genai,
    ):
        mock_instructor_client = MagicMock()
        mock_instructor_client.chat.completions.create.side_effect = RuntimeError("API error")
        mock_from_genai.return_value = mock_instructor_client
        liaison = OperationalLiaison(api_key="test-key")

        result = await liaison.extract_metadata(
            streamed_text="Something about a break.",
            message="We are taking a break.",
        )

    assert isinstance(result, LiaisonMetadata)
    assert result.contact_pauses == []


# ── orchestrate_stream() ─────────────────────────────────────────────────────


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.insert_checkin = AsyncMock(return_value="test-id")
    db.get_latest_bio = AsyncMock(return_value=None)
    db.get_all_tasks = AsyncMock(return_value=[])
    db.get_all_vibes = AsyncMock(return_value=[])
    db.get_recent_bio = AsyncMock(return_value=[])
    db.get_behavioral_summary = AsyncMock(return_value=None)
    db.get_behavioral_profiles = AsyncMock(return_value=[])
    db.upsert_contact_pause = AsyncMock(return_value=None)
    db.get_active_pauses = AsyncMock(return_value=[])
    db.complete_task = AsyncMock(return_value=None)
    return db


async def _fake_stream_text(*args: object, **kwargs: object) -> AsyncGenerator[str, None]:
    yield "chunk-one"
    yield "chunk-two"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrate_stream_yields_agents_event_first() -> None:
    """orchestrate_stream() first event is 'agents' containing overall_status."""
    with (
        patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls,
        patch("kinetic.orchestrator.lead.detect_and_update_patterns", new_callable=AsyncMock),
    ):
        mock_liaison = MagicMock()
        mock_liaison.stream_text = MagicMock(return_value=_fake_stream_text())
        mock_liaison.extract_metadata = AsyncMock(return_value=LiaisonMetadata())
        mock_liaison_cls.return_value = mock_liaison

        events: list[dict[str, str]] = []
        async for event in orchestrate_stream(
            CheckInPayload(),
            message="Check-in.",
            db=_mock_db(),
        ):
            events.append(event)

    assert len(events) >= 1
    first = events[0]
    assert first["event"] == "agents"
    payload = json.loads(first["data"])
    assert "overall_status" in payload


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrate_stream_yields_token_events() -> None:
    """orchestrate_stream() yields one 'token' event per chunk from stream_text."""
    with (
        patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls,
        patch("kinetic.orchestrator.lead.detect_and_update_patterns", new_callable=AsyncMock),
    ):
        mock_liaison = MagicMock()
        mock_liaison.stream_text = MagicMock(return_value=_fake_stream_text())
        mock_liaison.extract_metadata = AsyncMock(return_value=LiaisonMetadata())
        mock_liaison_cls.return_value = mock_liaison

        events: list[dict[str, str]] = []
        async for event in orchestrate_stream(
            CheckInPayload(),
            message="Check-in.",
            db=_mock_db(),
        ):
            events.append(event)

    token_events = [e for e in events if e["event"] == "token"]
    assert len(token_events) == 2
    texts = [json.loads(e["data"])["text"] for e in token_events]
    assert texts == ["chunk-one", "chunk-two"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrate_stream_yields_done_event_last() -> None:
    """orchestrate_stream() final event is 'done' with responding_agent and active_pauses."""
    with (
        patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls,
        patch("kinetic.orchestrator.lead.detect_and_update_patterns", new_callable=AsyncMock),
    ):
        mock_liaison = MagicMock()
        mock_liaison.stream_text = MagicMock(return_value=_fake_stream_text())
        mock_liaison.extract_metadata = AsyncMock(return_value=LiaisonMetadata())
        mock_liaison_cls.return_value = mock_liaison

        events: list[dict[str, str]] = []
        async for event in orchestrate_stream(
            CheckInPayload(),
            message="Check-in.",
            db=_mock_db(),
        ):
            events.append(event)

    last = events[-1]
    assert last["event"] == "done"
    done_data = json.loads(last["data"])
    assert "responding_agent" in done_data
    assert "active_pauses" in done_data
    assert "contact_pauses" in done_data
    assert "task_completions" in done_data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrate_stream_event_order_agents_tokens_done() -> None:
    """Event order must be: agents → token* → done."""
    with (
        patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls,
        patch("kinetic.orchestrator.lead.detect_and_update_patterns", new_callable=AsyncMock),
    ):
        mock_liaison = MagicMock()
        mock_liaison.stream_text = MagicMock(return_value=_fake_stream_text())
        mock_liaison.extract_metadata = AsyncMock(return_value=LiaisonMetadata())
        mock_liaison_cls.return_value = mock_liaison

        events: list[dict[str, str]] = []
        async for event in orchestrate_stream(
            CheckInPayload(),
            message="Check-in.",
            db=_mock_db(),
        ):
            events.append(event)

    types = [e["event"] for e in events]
    assert types[0] == "agents"
    assert all(t == "token" for t in types[1:-1])
    assert types[-1] == "done"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrate_stream_persists_checkin() -> None:
    """orchestrate_stream() calls db.insert_checkin after streaming completes."""
    mock_db = _mock_db()
    with (
        patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls,
        patch("kinetic.orchestrator.lead.detect_and_update_patterns", new_callable=AsyncMock),
    ):
        mock_liaison = MagicMock()
        mock_liaison.stream_text = MagicMock(return_value=_fake_stream_text())
        mock_liaison.extract_metadata = AsyncMock(return_value=LiaisonMetadata())
        mock_liaison_cls.return_value = mock_liaison

        async for _ in orchestrate_stream(
            CheckInPayload(),
            message="Check-in.",
            db=mock_db,
        ):
            pass

    mock_db.insert_checkin.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrate_stream_survives_agent_failure() -> None:
    """orchestrate_stream() continues and yields done even when a specialist agent raises."""
    with (
        patch("kinetic.orchestrator.lead.BioArchivist") as mock_bio_cls,
        patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls,
        patch("kinetic.orchestrator.lead.detect_and_update_patterns", new_callable=AsyncMock),
    ):
        mock_bio_cls.return_value.process = AsyncMock(side_effect=RuntimeError("bio down"))
        mock_liaison = MagicMock()
        mock_liaison.stream_text = MagicMock(return_value=_fake_stream_text())
        mock_liaison.extract_metadata = AsyncMock(return_value=LiaisonMetadata())
        mock_liaison_cls.return_value = mock_liaison

        events: list[dict[str, str]] = []
        async for event in orchestrate_stream(
            CheckInPayload(),
            message="Check-in.",
            db=_mock_db(),
        ):
            events.append(event)

    types = [e["event"] for e in events]
    assert types[0] == "agents"
    assert types[-1] == "done"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrate_stream_applies_contact_pause() -> None:
    """orchestrate_stream() calls upsert_contact_pause for each directive in metadata."""
    mock_db = _mock_db()
    pause = ContactPauseDirective(person="Alex", pause_days=7)
    with (
        patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls,
        patch("kinetic.orchestrator.lead.detect_and_update_patterns", new_callable=AsyncMock),
    ):
        mock_liaison = MagicMock()
        mock_liaison.stream_text = MagicMock(return_value=_fake_stream_text())
        mock_liaison.extract_metadata = AsyncMock(
            return_value=LiaisonMetadata(contact_pauses=[pause])
        )
        mock_liaison_cls.return_value = mock_liaison

        async for _ in orchestrate_stream(
            CheckInPayload(),
            message="We're on a pause.",
            db=mock_db,
        ):
            pass

    mock_db.upsert_contact_pause.assert_called_once()
    call_args = mock_db.upsert_contact_pause.call_args[0]
    assert call_args[0] == "Alex"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrate_stream_applies_task_completion() -> None:
    """orchestrate_stream() calls complete_task for each completion in metadata."""
    mock_db = _mock_db()
    with (
        patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls,
        patch("kinetic.orchestrator.lead.detect_and_update_patterns", new_callable=AsyncMock),
    ):
        mock_liaison = MagicMock()
        mock_liaison.stream_text = MagicMock(return_value=_fake_stream_text())
        mock_liaison.extract_metadata = AsyncMock(
            return_value=LiaisonMetadata(task_completions=["laundry"])
        )
        mock_liaison_cls.return_value = mock_liaison

        async for _ in orchestrate_stream(
            CheckInPayload(),
            message="I finished the laundry.",
            db=mock_db,
        ):
            pass

    mock_db.complete_task.assert_called_once_with("laundry")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_orchestrate_stream_handles_missing_task_gracefully() -> None:
    """orchestrate_stream() does not raise when complete_task raises KeyError."""
    mock_db = _mock_db()
    mock_db.complete_task = AsyncMock(side_effect=KeyError("laundry"))
    with (
        patch("kinetic.orchestrator.lead.OperationalLiaison") as mock_liaison_cls,
        patch("kinetic.orchestrator.lead.detect_and_update_patterns", new_callable=AsyncMock),
    ):
        mock_liaison = MagicMock()
        mock_liaison.stream_text = MagicMock(return_value=_fake_stream_text())
        mock_liaison.extract_metadata = AsyncMock(
            return_value=LiaisonMetadata(task_completions=["laundry"])
        )
        mock_liaison_cls.return_value = mock_liaison

        events: list[dict[str, str]] = []
        async for event in orchestrate_stream(
            CheckInPayload(),
            message="Finished laundry.",
            db=mock_db,
        ):
            events.append(event)

    assert events[-1]["event"] == "done"
