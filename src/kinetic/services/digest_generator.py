from __future__ import annotations

import os
from datetime import datetime, timedelta

import structlog
from google import genai

from kinetic.db.base import DatabaseClient
from kinetic.models.outputs import BehavioralProfile, BehavioralSummary, DigestResponse

log = structlog.get_logger()

_MODEL = "gemini-2.5-flash"
_CACHE_TTL_HOURS = 6
_digest_cache: dict[str, DigestResponse] = {}

_NO_DATA_SUMMARY = "No check-in data yet. Start briefing Kinetic to build your weekly digest."


async def generate_digest(
    db: DatabaseClient,
    api_key: str,
    tenant: str,
    *,
    force: bool = False,
) -> DigestResponse:
    """Generate or return a cached weekly digest for the given tenant.

    Caches results for _CACHE_TTL_HOURS hours per tenant. force=True bypasses
    the cache and always regenerates. Never raises — Gemini errors are captured
    in the returned summary string.
    """
    if not force and tenant in _digest_cache:
        cached = _digest_cache[tenant]
        if datetime.now() - cached.generated_at < timedelta(hours=_CACHE_TTL_HOURS):
            log.info("digest.cache.hit", tenant=tenant)
            return cached

    summary = await db.get_behavioral_summary(days=14)
    profiles = await db.get_behavioral_profiles()
    history = await db.get_history(limit=14)

    if summary.days_analyzed == 0 and not history:
        result = DigestResponse(summary=_NO_DATA_SUMMARY, generated_at=datetime.now())
        _digest_cache[tenant] = result
        return result

    log.info("digest.generate.start", tenant=tenant)
    try:
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        client = genai.Client(api_key=resolved_key)
        prompt = _build_digest_prompt(summary, profiles, history)
        response = await client.aio.models.generate_content(
            model=_MODEL,
            contents=prompt,
        )
        text = (response.text or "").strip() or _NO_DATA_SUMMARY
        log.info("digest.generate.done", tenant=tenant)
    except Exception as e:
        log.exception("digest.generate.error", tenant=tenant)
        text = f"[DIGEST ERROR] {e}"

    result = DigestResponse(summary=text, generated_at=datetime.now())
    _digest_cache[tenant] = result
    return result


def _build_digest_prompt(
    summary: BehavioralSummary,
    profiles: list[BehavioralProfile],
    history: list[dict[str, str]],
) -> str:
    lines: list[str] = [
        "You are the Operational Liaison for Kinetic, a personal infrastructure system.",
        "Write a single plain-English paragraph (3-5 sentences) summarising the user's",
        "last 14 days across bio, logistics, and relational domains. Be direct and clinical.",
        "Highlight the most important pattern or risk. No markdown, no bullet points.",
        "",
        "BEHAVIORAL SUMMARY (14 days):",
    ]

    if summary.bio_trend:
        bt = summary.bio_trend
        lines.append(
            f"Sleep: avg {bt.avg_sleep_hours:.1f} hrs/night, "
            f"slope {bt.sleep_slope:+.2f} hrs/day. "
            f"Nutrition: {bt.avg_nutrition:.1f}/10. Energy: {bt.avg_energy:.1f}/10."
        )
        if bt.worst_sleep_day:
            lines.append(f"Worst sleep day: {bt.worst_sleep_day}.")
    else:
        lines.append("No bio data in this period.")

    if summary.recurring_tasks:
        lines.append("Recurring overdue tasks:")
        for t in summary.recurring_tasks:
            lines.append(
                f"  - {t.name}: overdue {t.times_overdue}x, avg {t.avg_days_overdue:.1f} days late"
            )
    else:
        lines.append("No recurring overdue tasks.")

    if summary.relational_drifts:
        lines.append("Relational drifts:")
        for d in summary.relational_drifts:
            lines.append(
                f"  - {d.person}: contact trend {d.contact_trend:+.2f} days/check-in, "
                f"last contact {d.last_known_days_since_contact} days ago"
            )
    else:
        lines.append("No relational drifts detected.")

    if profiles:
        lines.append(f"\nPersistent behavioral patterns ({len(profiles)} on file):")
        for p in profiles[:3]:
            lines.append(f"  - {p.profile_key}: {p.insight}")

    if history:
        lines.append(f"\nLast {min(len(history), 5)} check-in messages (oldest first):")
        for entry in history[-5:]:
            role = entry.get("role", "user")
            content = entry.get("content", "")[:200]
            lines.append(f"  [{role}]: {content}")

    return "\n".join(lines)
