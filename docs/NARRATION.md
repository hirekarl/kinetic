# Kinetic — Video Narration Script

**Target runtime:** ~4:00
**Format:** Narration track laid over three video sources:
- Stock footage or title cards (intro and outro)
- Playwright screen recording (demo section)

Narration is written to be read aloud at a natural pace (~130 wpm). Sections marked
`[HOLD]` are intentional silence — let the visual communicate.

---

## PART ONE — INTRO
*[Stock footage or dark title card. "Kinetic" logotype on screen.]*
*Approximate length: 1:10*

---

Jordan is a senior engineer running at full load. By every external measure — output,
velocity, shipping — Jordan is performing.

But there's a cost those measures don't show.

Sleep goes first. Not dramatically — just an hour here, forty minutes there, until the
average quietly drops below six. Domestic tasks accumulate until one of them becomes a
crisis. Relationships don't break; they go quiet, over weeks, through no particular
decision.

And every morning, before Jordan has done a single piece of real work, thirty to
forty-five minutes disappear to a question he can't answer clearly: what is actually
most important right now? Across biological, logistics, relationships — three separate domains,
no shared language, no priority rank, and a brain already running on a deficit.

`[HOLD — 3 seconds]`

The root cause is a familiar one for engineers: no instrumentation.

Engineers instrument everything at work. Dashboards, alerts, runbooks. But they run
their personal infrastructure completely blind. No SLO for sleep. No alerting on
relational drift. No triage queue for domestic logistics.

The tools that exist solve one domain in isolation. None of them synthesize across
domains. None of them tell Jordan what to do first.

`[HOLD — 2 seconds]`

Kinetic is a personal infrastructure management system. One natural-language check-in,
once a day. Three specialist AI agents run in parallel. One prioritized triage list
comes back — the two or three actions that stop the most accumulating debt right now,
so Jordan can stop deliberating and start moving.

The stack: Gemini 2.5 Flash with Instructor for structured LLM parsing, FastAPI and
Pydantic on the backend, React and TypeScript on the frontend. Responses stream
token-by-token over Server-Sent Events. Data persists to SQLite locally, PostgreSQL
on Render in production.

`[HOLD — 2 seconds. Transition to screen recording.]`

---

## PART TWO — SCREEN RECORDING
*[Cut to Playwright demo video. Narration is approximate — adjust to picture in editing.]*
*Approximate length: 2:20*

---

### Login

*[Video: login screen. Wrong password typed. Error alert appears.]*

Wrong credentials — clear error state, clear message. No raw exception. A path forward.

`[HOLD — let the correct login play through]`

---

### Onboarding

*[Video: three-screen onboarding modal.]*

First-time users see a brief onboarding — three screens, keyboard-navigable, WCAG 2.1
AA tested.

`[HOLD — let the three clicks play through]`

---

### Historical context

*[Video: Simulate Week click, dashboard populates, Behavioral Profile expands.]*

Simulate Week inserts five pre-scripted check-ins across seven historical days —
seeding a week of behavioral data without a real week of waiting.

`[HOLD — 2 seconds while profile panel is visible]`

This is the Behavioral Profile. Jordan has been falling below six hours of sleep on
weekdays for five consecutive observations. Gemini identified that pattern from the
accumulated history — not from rules or templates. The system built a picture of
Jordan's week that Jordan, inside it, couldn't see.

`[HOLD — 2 seconds while Weekly Digest is visible]`

The Weekly Digest is a separate Gemini call: a prose summary of the full week's
trajectory, cached for six hours. Before Jordan types a single word, the Operational
Liaison has already read it. The system walks in briefed.

---

### Turn 1 — The crisis

*[Video: chat input focused, Send button visibly disabled, typing begins.]*

Empty input — Send is disabled. Jordan can't submit noise.

`[HOLD — let the typing play out]`

One message. All three domains. Everything that has been competing for Jordan's
attention, said once, in plain language. That is the entire interaction cost.

`[HOLD — watch the 3-second loading state]`

One Gemini call parses the message into a typed Pydantic model. The lead orchestrator
routes to all three agents in parallel. The Liaison streams the response back over
Server-Sent Events.

`[HOLD — watch the dashboard update to RED]`

The dashboard reflects what Jordan already felt but couldn't quantify.

Bio-Metric Archivist: burnout score 82. The scale runs 0 to 100 — above 75 is a
CRITICAL flag. That number is computed from a seven-day sleep trend using weighted
decay: recent nights count more heavily than last week's. Jordan hasn't been imagining
the fatigue. The decline is real, measured, and now visible.

`[HOLD — as camera scrolls to logistics]`

Logistics Fixer: laundry six days overdue. The agent breaks the task into steps and
runs the numbers — 120 minutes to handle in-house, minimal overhead to outsource.
The gap between those figures is the ROI. Jordan didn't have to think through that
trade-off. The system already worked it out.

Relational Diplomat: connection margin score for Marcus has dropped to 35 out of 100.
The system proposes the smallest effective action — a five-minute voice memo — because
it understands Jordan's current bandwidth.

For the first time this week, Jordan has the full picture. And a place to start.

---

### Turn 2 — Multi-turn ROI

*[Video: second message typed, sent, response appears.]*

Jordan follows up. Same session, full context — no re-explaining, no starting over.

`[HOLD — watch the loading state and response]`

120 minutes of focus time reclaimed. Projected burnout reduction: 15.5 points on the
same 0-to-100 scale. That figure comes from the expected sleep improvement if Jordan
uses those freed hours — fed back through the burnout formula. Jordan didn't have to
run that scenario. The system ran it while Jordan was still forming the question.

The ROI card puts a number on what inaction costs. Jordan can see the trade-off, make
a decision, and move on. The deliberation is done.

---

### Task completion

*[Video: triage list, checkbox clicked, dashboard updates.]*

The triage list ranks actions from 1 to 10 across all three domains simultaneously —
bio, logistics, relational, already weighed against each other. Jordan doesn't have to
choose between them or hold the trade-off in his head. He picks up the top item.

Laundry Protocol: done. The list re-ranks. ROI margin updates to 22 percent — 22
percent of Jordan's weekly focus hours, recovered. One decision. Visible progress.

---

### Turn 3 — Recovery

*[Video: third message sent, status lifts to yellow.]*

Jordan confirms the action. Status lifts from red to yellow. Logistics goes green.

One sector resolved. Attention shifts to what's left.

---

### Error handling

*[Video: message sent, error banner appears.]*

What happens when the analysis engine goes down.

The app catches the 503 and shows a clear message. Never a stack trace.

`[HOLD — let the error banner sit for a moment]`

One button: Retry. The last message replays without a page reload. Jordan doesn't lose
context. Doesn't have to start over.

`[HOLD — watch the recovery response appear]`

---

### Agent Dispatch Log

*[Video: dispatch log expands, first entry opens.]*

Every check-in logged — which agent responded, what it found, when. Full routing audit.
Jordan can always see what fired and why.

---

### Mobile

*[Video: viewport resizes to 390px, stacked mobile layout appears.]*

Responsive layout. Chat panel stacks above the dashboard at mobile width. Same data,
same triage, same interactions — wherever Jordan is when the morning hits.

`[HOLD — 2 seconds. Cut back to title card or stock footage.]`

---

## PART THREE — OUTRO
*[Title card or stock footage. "What's Next."]*
*Approximate length: 0:30*

---

The most valuable next feature is proactive push.

Right now, Jordan briefs Kinetic. The next step reverses that. Every morning, before
the thirty-minute triage fog sets in — before Jordan has to ask — Kinetic runs a
background pass from the previous night's data. Sleep trend, task state, relational
drift. One notification. Three priorities, already ranked.

Jordan opens the day knowing exactly where his attention belongs.

`[HOLD — 3 seconds. Fade to black or end card.]`

---

*Kinetic — Bio-Operational Triage Engine*
*Pursuit AI-Native L1 Capstone — Karl Johnson*
