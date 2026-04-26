# Kinetic — Demo Script

**Audience:** Pursuit AI-Native L1 capstone reviewers
**Duration:** ~10 minutes
**Setup:** Two terminals already running (see Pre-Demo Checklist below)

---

## Pre-Demo Checklist

Run these before presenting. Takes about 90 seconds.

```bash
# Terminal 1 — seed demo history, then start backend
cd /path/to/kinetic
uv run python scripts/seed_demo.py
uv run uvicorn kinetic.main:app --reload --port 8000

# Terminal 2 — start frontend
cd frontend && npm run dev
```

Open `http://localhost:5173` in a browser. Confirm:
- [ ] The onboarding modal appears (means localStorage is fresh — good)
- [ ] Backend terminal shows no errors

If the onboarding modal does NOT appear (already dismissed), open DevTools → Application → Local Storage → delete `kinetic_onboarded`, then reload.

---

## The Narrative

> *It's 9pm on a Wednesday. Karl is deep in a late-night build sprint — code is flowing, productivity at its peak. Running quietly alongside his IDE, Kinetic's dashboard is about to surface a yellow warning. Sleep debt is quietly accumulating. Laundry crossed its critical threshold six days ago. And his connection margin with Marcus has been in the red for over a week.*
>
> *Prior to Kinetic, Karl's only feedback loop was burnout. Now, instead of becoming a crisis, he gets a prioritized triage list: clear three high-leverage actions in under five minutes, then return to flow.*

---

## Step-by-Step Walkthrough

### Step 1 — First Visit: Onboarding (≈1 min)

The 3-screen modal appears automatically on first visit.

**Say:** "Kinetic opens with a brief tutorial. Three screens — you can skip at any point."

Walk through:
1. **Personal Infrastructure** — "Not a wellness app. Personal systems management."
2. **Chat-First** — "Natural language in, structured triage out."
3. Click **Done** to dismiss.

**Point out:** The modal is keyboard-navigable and passes full WCAG 2.1 AA (axe-core tested).

---

### Step 2 — System at Rest: Behavioral History (≈2 min)

The dashboard shows **System Idle** — no data has been submitted *today*, but history exists from the seed script.

**Say:** "The system already has seven days of behavioral history. Let me show you what it's learned."

Scroll down on the right panel. Click **Behavioral Profile** to expand the disclosure section.

**Point to:**
- `chronic_sleep_deficit` — "Sleep has been declining ~0.3 hours per day this week."
- `marcus_relational_drift` — "Contact with Marcus has been drifting — days since contact doubled in a week."

**Say:** "These patterns were synthesized by Gemini from the accumulated check-in history. They ground the Operational Liaison's tactical guidance in what's actually been happening, not just today's snapshot."

---

### Step 3 — Live Check-In: The PRD Narrative (≈3 min)

In the left-panel chat input, type exactly:

```
Slept 5 hours, ate okay, feeling disconnected from Marcus.
```

Click **Send** (or press Enter).

**While it loads, say:** "One LLM call — Gemini 2.5 Flash + Instructor parses this into a typed `CheckInPayload`. The lead orchestrator routes to whichever agents are relevant. All three fire here."

**When the dashboard populates, walk through each card:**

**Bio-Metric Archivist (top-left card):**
- "Burnout score. Weighted: sleep 40%, nutrition 30%, energy 30%."
- "Forecast from the agent: plain English, non-alarming."
- "Status light: yellow — degraded but not critical."

**Logistics Fixer (top-center card):**
- "Laundry has been overdue six days — it crossed the critical threshold and surfaced here."
- "Outsourcing ROI: the agent suggests delegation with a time-reclaim estimate."

**Relational Diplomat (top-right card):**
- "Connection margin score for Marcus — recency-decayed. 11 days since contact, vibe 4/10."
- "Interaction sprint: a concrete, time-bounded action."

---

### Step 4 — Triage List (≈1 min)

Scroll down to **Prioritized Triage**.

**Say:** "The orchestrator merges all agent outputs into one flat, priority-sorted list. One place, one decision. The Operational Liaison wrote these action steps — it translates agent findings into clinical micro-tasks to break decision paralysis."

Point to the triage items:
- Priority 9 (Bio) — sleep intervention
- Priority 6 (Logistics) — laundry
- Priority 6 (Relational) — Marcus outreach

---

### Step 5 — ROI Summary (≈1 min)

Scroll down to **Performance Yield & ROI**.

**Say:** "The ROI card quantifies operational yield. Time recovered through outsourcing suggestions. System margin delta. Projected burnout risk reduction if these items are resolved."

**Say:** "This is the capstone metric — proof that the system doesn't just report problems, it quantifies the cost of inaction and the value of each recommended action."

---

### Step 6 — Architecture Questions (≈2 min)

Common reviewer questions and talking points:

**"How does the LLM parsing work?"**
> Gemini 2.5 Flash with Instructor enforces a typed `CheckInPayload` Pydantic model. One call per check-in. The orchestrator never touches raw text — it receives a clean, validated, typed payload.

**"What if an agent fails?"**
> Each agent runs in an isolated try/except in the orchestrator. One failure degrades that card to an "Agent unavailable" state while the others still run. The overall status reflects worst-case. Show the error state by clicking Reset System and submitting without a backend.

**"Where is the data stored?"**
> SQLite locally at `./kinetic.db`. All single-user, fully private. The behavioral profile table accumulates Gemini-derived pattern insights across sessions — that's what the Behavioral Profile panel shows.

**"Why not stream the response?"**
> Deliberate scope decision for the MVP. The loading indicator and immediate card update on resolution gives the same perceived experience without streaming complexity.

---

## If Something Goes Wrong

| Problem | Fix |
|---------|-----|
| "Analysis unavailable" error banner | GEMINI_API_KEY not set — check `.env` and restart backend |
| Onboarding modal doesn't appear | DevTools → Local Storage → delete `kinetic_onboarded` → reload |
| Dashboard shows blank cards after check-in | Backend not running on :8000 — restart Terminal 1 |
| Behavioral Profile panel shows empty state | Re-run `uv run python scripts/seed_demo.py` and reload |

---

## Post-Demo

Run the reset if handing off to another reviewer:

```bash
curl -X POST http://localhost:8000/api/debug/reset
```

Or click **Reset System** in the top-right of the dashboard.
