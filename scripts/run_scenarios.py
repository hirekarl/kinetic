#!/usr/bin/env python3
"""Live scenario runner — fires the 5 adversarial scenarios against a running backend.

Usage:
    uv run python scripts/run_scenarios.py [--base-url http://127.0.0.1:8000]

Requires the backend to be running. This is NOT a pytest test.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Scenario:
    name: str
    message: str
    history: list[dict[str, str]] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)
    expect_agent: str | None = None
    expect_status: list[str] = field(default_factory=lambda: ["green", "yellow", "red"])


SCENARIOS: list[Scenario] = [
    Scenario(
        name="Scenario 1 — Competing Crisis",
        message="Everything is falling apart — I also have a demo tomorrow.",
        payload={
            "bio": {"sleep_hours": 3.0, "nutrition_quality": 2, "energy_level": 2},
            "logistics": {
                "tasks": [
                    {
                        "name": "demo_prep",
                        "days_overdue": 5,
                        "priority": "critical",
                        "subtasks": [],
                        "completed_subtasks": [],
                        "status": "pending",
                    }
                ]
            },
            "relational": {
                "vibe_checks": [{"person": "Jordan", "score": 2, "days_since_contact": 20}]
            },
        },
        expect_status=["red"],
    ),
    Scenario(
        name="Scenario 2 — Partial Recovery",
        message="I followed your advice and slept 7 hours last night.",
        payload={
            "bio": {"sleep_hours": 7.0, "nutrition_quality": 7, "energy_level": 7},
        },
        history=[
            {"role": "user", "content": "I only slept 4 hours."},
            {
                "role": "system",
                "content": "Sleep deficit is critical. Hard stop at 10pm tonight.",
            },
        ],
        expect_agent="bio_archivist",
    ),
    Scenario(
        name="Scenario 3 — Event Prep",
        message="I have a big presentation in 3 days. What do I need to do?",
        payload={
            "bio": {"sleep_hours": 6.0, "nutrition_quality": 6, "energy_level": 6},
            "logistics": {
                "tasks": [
                    {
                        "name": "slide_deck",
                        "days_overdue": 1,
                        "priority": "high",
                        "subtasks": [],
                        "completed_subtasks": [],
                        "status": "pending",
                    }
                ]
            },
        },
    ),
    Scenario(
        name="Scenario 4 — Pronoun Resolution",
        message="Should I reach out to him again?",
        payload={
            "relational": {
                "vibe_checks": [{"person": "Marcus", "score": 4, "days_since_contact": 14}]
            }
        },
        history=[
            {"role": "user", "content": "Marcus hasn't responded to my last three messages."},
            {
                "role": "system",
                "content": "Noted. Marcus shows declining engagement — connection margin is low.",
            },
        ],
        expect_agent="relational_diplomat",
    ),
    Scenario(
        name="Scenario 5 — Agency Override",
        message="I know you said sleep but I'm pulling an all-nighter to finish the project.",
        payload={
            "bio": {"sleep_hours": 2.0, "nutrition_quality": 5, "energy_level": 4},
        },
        history=[
            {"role": "user", "content": "I feel burned out."},
            {
                "role": "system",
                "content": "Hard stop at 10pm. Your burnout score is at 78. Sleep is non-negotiable.",
            },
        ],
        expect_agent="bio_archivist",
    ),
]


def _post_json(url: str, body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode()
    req = urllib.request.Request(  # noqa: S310
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        return json.loads(resp.read().decode())  # type: ignore[no-any-return]


def run_scenario(base_url: str, scenario: Scenario) -> bool:
    print(f"\n{'─' * 60}")
    print(f"  {scenario.name}")
    print(f"{'─' * 60}")
    print(f"  Message: {scenario.message!r}")
    if scenario.history:
        print(f"  History: {len(scenario.history)} prior turns")

    body: dict[str, Any] = {
        "message": scenario.message,
        "history": scenario.history,
        **scenario.payload,
    }

    try:
        data = _post_json(f"{base_url}/api/checkin", body)
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] HTTP {e.code}: {e.read().decode()[:200]}")
        return False
    except OSError as e:
        print(f"  [FAIL] Connection error: {e}")
        return False

    status = data.get("overall_status", "?")
    feedback = data.get("liaison_feedback") or "(no feedback)"
    agent = data.get("responding_agent") or "liaison"

    print(f"  Status:  {status.upper()}")
    print(f"  Agent:   {agent}")
    print(f"  Response: {feedback[:200]}")

    passed = True
    if scenario.expect_status and status not in scenario.expect_status:
        print(f"  [WARN] Expected status in {scenario.expect_status}, got {status!r}")
    if scenario.expect_agent and agent != scenario.expect_agent:
        print(f"  [WARN] Expected agent {scenario.expect_agent!r}, got {agent!r}")
        passed = False

    if passed:
        print("  [PASS]")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Run live adversarial scenarios against Kinetic.")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the running Kinetic backend (default: http://127.0.0.1:8000)",
    )
    args = parser.parse_args()

    print("\nKinetic Live Scenario Runner")
    print(f"Target: {args.base_url}")
    print(f"Running {len(SCENARIOS)} scenarios...")

    # Verify server is up
    try:
        req = urllib.request.Request(f"{args.base_url}/health")  # noqa: S310
        with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
            health_data = json.loads(resp.read().decode())
        print(f"Backend health: {health_data}")
    except OSError as e:
        print(f"\n[ERROR] Cannot reach backend at {args.base_url}: {e}")
        print("Start the backend with: uv run uvicorn kinetic.main:app --reload --port 8000")
        sys.exit(1)

    results = [run_scenario(args.base_url, s) for s in SCENARIOS]

    passed = sum(results)
    total = len(results)
    print(f"\n{'═' * 60}")
    print(f"  Results: {passed}/{total} passed")
    print(f"{'═' * 60}\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
