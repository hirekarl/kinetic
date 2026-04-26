from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

from google import genai

from kinetic.db.sqlite_client import SqliteClient
from kinetic.models.outputs import BehavioralProfile, BehavioralSummary

logger = logging.getLogger(__name__)

_GUARD_HOURS = 20
_MIN_DAYS = 3
_MAX_PATTERNS = 5


async def detect_and_update_patterns(
    db: SqliteClient,
    behavioral_summary: BehavioralSummary,
    current_profiles: list[BehavioralProfile],
    api_key: str | None = None,
) -> None:
    """Derive behavioral patterns from accumulated data and persist them.

    Runs as an asyncio.create_task() — never raises.
    """
    if behavioral_summary.days_analyzed < _MIN_DAYS:
        logger.info(
            "Pattern detection skipped: insufficient history (%d days)",
            behavioral_summary.days_analyzed,
        )
        return

    cutoff = behavioral_summary.generated_at - timedelta(hours=_GUARD_HOURS)
    if any(p.last_updated > cutoff for p in current_profiles):
        logger.info("Pattern detection skipped: profiles updated recently")
        return

    try:
        key = api_key or os.environ.get("GEMINI_API_KEY")
        client = genai.Client(api_key=key)

        prompt = _build_prompt(behavioral_summary, current_profiles)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        raw = response.text or ""
        patterns = _parse_patterns(raw)

        now = datetime.now()
        for entry in patterns:
            if not _is_valid_entry(entry):
                logger.warning("Skipping malformed pattern entry: %s", entry)
                continue
            profile = BehavioralProfile(
                profile_key=entry["profile_key"],
                insight=entry["insight"],
                evidence=entry.get("evidence", {}),
                first_observed=now,
                last_updated=now,
                observation_count=1,
            )
            await db.upsert_behavioral_profile(profile)

    except Exception:
        logger.exception("Pattern detection failed — background task suppressing error")


def _build_prompt(
    summary: BehavioralSummary,
    profiles: list[BehavioralProfile],
) -> str:
    lines: list[str] = ["BEHAVIORAL SUMMARY:"]

    if summary.bio_trend:
        bt = summary.bio_trend
        lines.append(
            f"Sleep: avg {bt.avg_sleep_hours:.1f} hrs/night, "
            f"slope {bt.sleep_slope:+.2f} hrs/day over {bt.days_analyzed} days"
        )
        lines.append(f"Nutrition score: {bt.avg_nutrition:.1f}/10")
        lines.append(f"Energy score: {bt.avg_energy:.1f}/10")
        if bt.worst_sleep_day:
            lines.append(f"Worst sleep day: {bt.worst_sleep_day}")

    if summary.recurring_tasks:
        lines.append("Recurring overdue tasks:")
        for t in summary.recurring_tasks:
            lines.append(
                f"  - {t.name} ({t.times_overdue}x overdue, "
                f"avg {t.avg_days_overdue:.1f} days late, priority={t.priority})"
            )

    if summary.relational_drifts:
        lines.append("Relational drifts (contact declining):")
        for d in summary.relational_drifts:
            lines.append(
                f"  - {d.person}: trend {d.contact_trend:+.2f} days/check-in, "
                f"avg vibe {d.avg_vibe_score:.1f}/10, "
                f"last contact {d.last_known_days_since_contact} days ago"
            )

    if profiles:
        lines.append("\nEXISTING PATTERNS:")
        for p in profiles:
            lines.append(f"  - {p.profile_key}: {p.insight}")

    lines.append(
        f"\nReturn a JSON array (max {_MAX_PATTERNS} items) of behavioral patterns. "
        "Each object must have exactly these keys:\n"
        '  "profile_key" (snake_case string),\n'
        '  "insight" (plain English sentence),\n'
        '  "evidence" (JSON object with supporting data points)\n'
        "Return ONLY the JSON array — no markdown fences, no commentary."
    )

    return "\n".join(lines)


def _parse_patterns(text: str) -> list[dict[str, Any]]:
    """Extract a JSON array from Gemini response text.

    Uses bracket-depth matching from the last ']' backwards to find the
    outermost array. Handles nested arrays and prose with brackets before
    the JSON payload (e.g. "Here [per request]. Data: [...]").
    """
    end = text.rfind("]")
    if end == -1:
        raise ValueError(f"No JSON array found in response: {text[:200]}")
    depth = 0
    for i in range(end, -1, -1):
        if text[i] == "]":
            depth += 1
        elif text[i] == "[":
            depth -= 1
            if depth == 0:
                return json.loads(text[i : end + 1])  # type: ignore[no-any-return]
    raise ValueError(f"Unmatched brackets in response: {text[:200]}")


def _is_valid_entry(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    return all(k in entry for k in ("profile_key", "insight", "evidence"))
