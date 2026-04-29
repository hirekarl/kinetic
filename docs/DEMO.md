# Kinetic — Live Presentation Script

**Presentation date:** Wednesday, May 6, 2026
**Total duration:** 8–10 minutes
**Structure:** Problem → Root Cause → Solution → Live Demo → What's Next

---

## Pre-Demo Setup (do this before anyone is watching)

```bash
# Terminal 1 — backend
uv run uvicorn kinetic.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

Open `http://localhost:5173` in Chrome. Then:

1. Log in as `demo` / `demo`
2. Click **Simulate Week** — wait for the dashboard to populate (~3s)
3. Log out
4. Open DevTools → Application → Local Storage → delete `kinetic_onboarded`
5. Reload the page — the login screen should appear

**Confirm before starting:**
- [ ] Login screen is showing (not the dashboard)
- [ ] Backend terminal shows no errors
- [ ] You have your three check-in messages ready (below)

**If Simulate Week fails:** `uv run python scripts/seed_demo.py` seeds the DB directly.

---

## Section 1 — Problem (≈90 seconds, no keyboard)

> **Say:**
>
> "Jordan is a senior engineer running at capacity — shipping features, managing stakeholders, staying current. By conventional metrics, Jordan is performing well. But there's a hidden cost."
>
> "Sleep is the first thing to slip. Then domestic tasks pile up — quietly, until something breaks. Then relationships drift — not through neglect, but through deferred priority. By the time Jordan notices any of this, the debt is already compounding."
>
> "The feedback loop today is burnout. The system only tells you something is wrong after the crash."
>
> "Jordan's specific pain: every morning, 30–45 minutes are lost deciding what's actually on fire across three completely separate domains — bio, logistics, relationships. No single source of truth. No priority rank. Just three open tabs and a vague feeling of being behind."

---

## Section 2 — Root Cause (≈60 seconds, no keyboard)

> **Say:**
>
> "The problem isn't discipline or time management. It's observability."
>
> "Engineers instrument everything at work. Dashboards, alerts, runbooks, on-call rotations. But they run their personal infrastructure completely blind. There's no SLO for sleep. No alerting on relational drift. No triage queue for domestic logistics."
>
> "Existing tools — sleep trackers, to-do apps, calendar reminders — each solve one domain in isolation. None of them synthesize across domains. None of them tell you *what to do first* given your current state across all three."
>
> "The result: Jordan makes prioritization decisions while sleep-deprived, with incomplete information, every single morning."

---

## Section 3 — Solution (≈45 seconds, no keyboard)

> **Say:**
>
> "Kinetic is a personal infrastructure management system. One check-in message — natural language, under 30 seconds — routes through three specialist AI agents. It returns a single prioritized triage list: the two or three actions that arrest the most compounding debt right now."
>
> "The stack: Gemini 2.5 Flash with Instructor for structured parsing, FastAPI and Pydantic on the backend, React and TypeScript on the frontend. Responses stream token-by-token over Server-Sent Events. Data persists to SQLite locally and PostgreSQL on Render in production."
>
> "Let me show you."

---

## Section 4 — Live Demo (≈6 minutes)

### 4.1 — Login and onboarding

**Action:** Type `demo` in the username field and `demo` in the password field.

> **Say:** "Demo tenant. Jordan's account."

**Action:** Click **Sign In**.

*The onboarding modal appears.*

> **Say:** "First-time experience. Three screens. Keyboard-navigable — axe-core tested for WCAG 2.1 AA compliance."

**Action:** Read the first screen briefly, then click **Next**.

> **Say:** "Not a wellness app. Personal systems management."

**Action:** Click **Next** on the second screen.

**Action:** Click **Done** on the third screen.

---

### 4.2 — Historical context: Simulate Week

> **Say:** "The system already has seven days of behavioral history pre-loaded. Let me show you what it's learned."

**Action:** Click **Simulate Week** in the top-right header.

*Wait ~2 seconds for the dashboard to populate.*

> **Say:** "Five check-ins across seven days — baseline health, gradual sleep decline, peak stress, early recovery."

**Action:** Scroll down on the right panel. Click **Behavioral Profile** to expand it.

> **Say:** "This profile was synthesized by Gemini from the accumulated history — not rules, not templates. The model identified a recurring pattern: Jordan's sleep consistently falls below six hours on weekdays. Five consecutive observations. The system tracks the trend, not just today's snapshot."

*Pause 4 seconds. Let the viewer read the profile.*

**Action:** Click **Behavioral Profile** again to collapse it. Then click **Weekly Review** to expand.

> **Say:** "The weekly digest is a separate Gemini call — prose synthesis of the full week's trajectory. AI-generated, cached for six hours. Jordan gets this before any check-in, so the Operational Liaison is already briefed."

*Pause 3 seconds.*

**Action:** Click **Weekly Review** to collapse it.

---

### 4.3 — Turn 1: The crisis check-in

**Action:** Click in the chat input. Hover over the **Send** button briefly to show it's disabled with empty input.

> **Say:** "Empty input — Send is disabled. Can't submit noise."

**Action:** Type this message slowly:

```
I'm completely overwhelmed. Four hours sleep, laundry six days overdue, haven't talked to Marcus in weeks.
```

> **Say (while typing):** "One message. All three domains. No form to fill, no category to choose — just brief it like a colleague."

**Action:** Press **Enter**.

> **Say (during the loading pause):** "One Gemini call to parse the message into a typed Pydantic model. The lead orchestrator routes to all three agents — Bio-Metric Archivist, Logistics Fixer, Relational Diplomat. They compute in parallel. The Operational Liaison then streams the response."

*The dashboard updates. Point to the bio card.*

> **Say:** "CRITICAL. Burnout score 82. The Bio-Metric Archivist computed this from four hours of sleep against Jordan's 7-day trend — not just today's number. Sleep sparkline on the right shows the decline curve. Burnout trend chart below it shows the trajectory."

*Scroll right panel slightly to show logistics card.*

> **Say:** "Logistics Fixer: laundry six days overdue, crossed the critical threshold. Look at the subtask breakdown — the agent didn't just flag it, it decomposed it into actionable steps. And it calculated the outsourcing ROI."

*Gesture to relational card.*

> **Say:** "Relational Diplomat: connection margin score 35, Marcus in the red. The agent proposed a five-minute voice memo as the minimal effective intervention."

---

### 4.4 — Turn 2: Multi-turn ROI follow-up

**Action:** Scroll back to the top of the right panel. Click in the chat input.

**Action:** Type:

```
How much time do I save if I outsource the laundry this week?
```

**Action:** Press **Enter**.

> **Say (during loading):** "Second turn. The system has the full conversation context — Jordan doesn't re-explain the situation."

*Dashboard updates.*

> **Say:** "120 minutes of focus time reclaimed. The Logistics Fixer calculated this from task complexity and the outsourcing suggestion it already had. Combined with the sleep protocol, 15.5-point projected burnout reduction. That's the ROI card — not just describing the problem, quantifying the cost of inaction."

---

### 4.5 — Task check-off and live dashboard update

**Action:** Scroll down to **Prioritized Triage**.

> **Say:** "One unified triage list. Priority-ranked across all three domains. Jordan doesn't have to choose between bio, logistics, and relationships — the system already did that."

**Action:** Point to the laundry item (priority 7). Click the checkbox to mark **Laundry Protocol** complete.

> **Say:** "Action taken. Watch the dashboard."

*The laundry item disappears from the triage list. ROI card updates.*

> **Say:** "Live update. The triage list re-ranks. ROI now shows 22% margin reclaimed. The system reflects the action immediately."

---

### 4.6 — Turn 3: Recovery confirmation

**Action:** Click in the chat input. Type:

```
I've outsourced the laundry. What's my status now?
```

**Action:** Press **Enter**.

*Dashboard updates to yellow.*

> **Say:** "Status lifts from red to yellow. Logistics sector is green. The system confirms the action closed the loop and redirects Jordan's attention to bio recovery — the remaining priority."

---

### 4.7 — Error handling and recovery

> **Say:** "One more thing — what happens when the analysis engine goes down?"

*[The demo will briefly show an error state — this is scripted.]*

**Action:** Click in the chat input. Type:

```
Can you give me a read on my sleep trajectory?
```

**Action:** Press **Enter**.

*After the loading indicator, an error banner appears at the top of the dashboard.*

> **Say:** "Graceful degradation. Meaningful message — not a stack trace. The system tells Jordan what went wrong, and offers a single action: Retry."

**Action:** Click **Retry**.

*Dashboard recovers. Response appears.*

> **Say:** "No page reload. The app recovers from a single component failure and replays the last message automatically."

---

### 4.8 — Agent Dispatch Log

**Action:** Scroll down to **Agent Dispatch Log** and click to expand it.

**Action:** Click the first entry to expand it.

> **Say:** "Full routing audit. Every check-in is logged with which agent responded, what it found, and when. Transparent AI — Jordan can always see what fired and why."

---

### 4.9 — Mobile responsiveness

> **Say:** "And it's responsive."

*[The demo will resize the viewport to mobile dimensions — this is scripted.]*

> **Say:** "Chat panel stacks above the dashboard at mobile width. Same data, same triage, same interactions. Scoped to desktop for this prototype but the layout holds."

---

## Section 5 — What's Next (≈60 seconds, no keyboard)

> **Say:**
>
> "The most valuable next feature is proactive push. Right now, Kinetic requires Jordan to brief it. The next step reverses that flow."
>
> "Every morning at 6am, Kinetic runs a background check-in from the previous night's data — sleep from wearable API, task state from the DB, relational drift from contact frequency. It synthesizes a triage list and pushes a single notification: *here are your top three actions for today, in priority order.*"
>
> "Jordan doesn't open an app. The system briefs Jordan. That's the product."

---

## If Something Goes Wrong

| Problem | Fix |
|---|---|
| "Analysis unavailable" error banner on real check-in | `GEMINI_API_KEY` not set — check `.env`, restart backend |
| Onboarding modal doesn't appear | DevTools → Local Storage → delete `kinetic_onboarded` → reload |
| Dashboard blank after check-in | Backend not running on `:8000` — restart terminal |
| Behavioral Profile shows "Building your profile" | Click Simulate Week again, or `uv run python scripts/seed_demo.py` |
| Simulate Week button not visible | Logged in as non-demo tenant — sign out, sign in as `demo` |
| Response takes > 30 seconds | Gemini rate limit — wait 60 seconds, retry |

## After the Demo

Click **Reset System** (top-right header) to wipe the database before the next run — or:

```bash
curl -X POST http://localhost:8000/api/debug/reset -H "Authorization: Bearer <token>"
```
