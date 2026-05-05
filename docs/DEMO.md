# Kinetic — Demo Script

**Format:** Loom · 5-part structure · 3–4 minutes total
**Presenter:** Karl Johnson

---

## Pre-Demo Setup

Do this before you hit record.

**Option A — Live deploy (recommended):** open [https://kinetic-frontend-c2bd.onrender.com](https://kinetic-frontend-c2bd.onrender.com) in Chrome.

> Note: Render free-tier services spin down after inactivity. If the page loads but check-ins time out, wait 30 seconds for the API to warm up, then retry.

**Option B — Local fallback** (if Render is unavailable):

```bash
# Terminal 1 — backend
uv run uvicorn kinetic.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

Open `http://localhost:5173` in Chrome.

**Then (either option):**

1. Log in as `demo` / `demo`
2. Click **Simulate Week** — wait for the dashboard to populate (~3s)
3. Log out
4. Open DevTools → Application → Local Storage → delete `kinetic_onboarded`
5. Reload the page — the login screen should appear

**Confirm before starting:**
- [ ] Login screen is showing (not the dashboard)
- [ ] Your three check-in messages are copied and ready to paste (below)

---

## 01 — The Builder · 15–30 sec

### Prose

"Hi, I'm Karl Johnson. I make AI middleware for the middle class.

This is Kinetic, a personal infrastructure management system. I built it in ten days on Python, FastAPI, and React, with Gemini 2.5 Flash handling the reasoning layer. Here's a problem a lot of us can relate to."

---

### Bullets

- Karl Johnson — full-stack engineer
- "I make AI middleware for the middle class"
- Kinetic — AI-Native L1 capstone, built in 10 days
- Stack: Python / FastAPI / React / Gemini 2.5 Flash

---

## 02 — The Problem · 30–45 sec

### Prose

"Jordan is 34, a senior engineer nine years into his career. He has an Oura ring, a task manager, and a weekly review habit he keeps… about two weeks out of four. He has all the tools. What he doesn't have is synthesis.

Every morning, 30 to 45 minutes disappear deciding what's actually on fire. Bio, logistics, relationships — pick your order. When the laundry piles up past five days, something else is already wrong too.

Jordan doesn't think of himself as burned out. He thinks of himself as behind. We all know what that feels like. It's not a discipline problem. It's an observability problem. That's the problem Kinetic solves."

---

### Bullets

- Jordan: 34, senior engineer at a Series B in Chicago — nine years in
- Has the tools: Oura ring, task manager, weekly review — just no synthesis across them
- Sleep slips → tasks pile → relationships drift
- **The thesis: not a discipline problem — an observability problem**
- 30–45 min lost every morning triaging across bio / logistics / relationships
- The laundry is the canary: piles past five days = something else is already wrong
- The only feedback loop is burnout — you find out after the crash

---

## 03 — Solution + Demo · 60–90 sec

### Prose

"Every day, you send one message to Kinetic — the same one you'd send a trusted colleague if you had 30 seconds. Three specialist AI agents analyze it and it comes back as a single prioritized triage list.

Here's what it looks like."

**[Action: log in as `demo` / `demo`]**

"This is Jordan's account. Watch what happens."

**[Action: click through onboarding → Done]**

"There's a short onboarding, three screens. It sets the right expectation. This isn't a wellness app, it's personal systems management."

**[Action: click Simulate Week, wait ~2 seconds]**

"Jordan has seven days of behavioral history already loaded. The Behavioral Profile on the right was synthesized by Gemini from those check-ins, not from rules or a template. It identified a real pattern in the data. Sleep was dropping below six hours on weekdays, five times in a row. The system tracks the trend, not just today's number.

Now I'll send a live check-in."

**[Action: type and send — paste slowly:]**

```
I'm completely overwhelmed. Four hours sleep, laundry six days overdue, haven't talked to Marcus in weeks.
```

"This one message covers all three domains, exactly how Jordan would text a trusted colleague. Three specialist agents analyze it simultaneously and the response comes back.

Burnout score 82. The threshold for critical is 75, and the sleep trend chart shows exactly how Jordan got there. Laundry is past the critical threshold and the system broke it into actionable subtasks with an outsourcing cost estimate. Marcus is flagged, with a five-minute voice memo suggested as the minimum effective intervention.

One list, ranked across all three domains. Jordan doesn't decide what matters most this morning. That decision is already made."

---

### Bullets

- One message → three specialist agents in parallel → one prioritized triage list
- Demo flow: login → onboarding → Simulate Week (7-day history) → live check-in
- Check-in: *"Four hours sleep, laundry overdue, haven't talked to Marcus in weeks"*
- Response comes back from all three agents
- Bio: burnout score 82 (critical), sleep sparkline shows the decline curve
- Logistics: laundry past critical threshold, decomposed into subtasks, outsourcing ROI calculated
- Relational: Marcus flagged — five-minute voice memo as minimum effective intervention
- Single triage list, cross-domain priority rank — Jordan doesn't decide, it's already done

---

## 04 — How It Works · 45–60 sec

### Prose

"There are two technical decisions I made that are worth calling out.

The first is structured outputs. Gemini parses Jordan's message using Instructor, a library that forces the model to return typed, validated data rather than freeform text. You either get a clean structured payload, or you get a loud error. There's no silent drift.

The second is parallelism. All three agents fire at the same time and their results get merged at the end. Running them in sequence would add two extra round-trips on every single check-in.

The same codebase also runs on SQLite locally and PostgreSQL in production."

---

### Bullets

- **Structured outputs:** Instructor forces Gemini to return validated, typed data — clean payload or loud error, no silent drift
- **Parallel agents:** all three fire simultaneously and results get merged — sequential would add two extra round-trips per check-in
- **Persistence:** same codebase, same interface — SQLite locally, PostgreSQL in production; the app doesn't know which one it has

---

## 05 — What's Next · 15–30 sec

### Prose

"What's next? Well, Jordan already has an Oura ring. He just can't get it to talk to anything useful.

Phase two for Kinetic will involve implementing passive data ingestion. Once Oura is set up to send automatic updates to Kinetic, the platform will brief Jordan each morning on schedule instead of waiting to be asked.

As an industry, we've built extraordinary observability tools for software. Jordan uses them every day and trusts them with production. We just haven't turned that lens on ourselves. Kinetic does.

Your infrastructure is showing. What are you going to do about it?"

---

### Bullets

- Jordan already has an Oura ring — just no integration that does anything useful with it
- Next: passive data ingestion so Jordan stops being the sensor
- Once in place: Kinetic briefs Jordan proactively — one morning notification, top three actions, no app to open
- Close: We've built observability for software. We just haven't turned that lens on ourselves. Kinetic does. Your infrastructure is showing. What are you going to do about it?

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Page loads but check-ins time out | Render API cold start — wait 30s, retry |
| "Analysis unavailable" error banner | `GEMINI_API_KEY` not configured on Render (or missing from `.env` locally) |
| Onboarding modal doesn't appear | DevTools → Local Storage → delete `kinetic_onboarded` → reload |
| Dashboard blank after check-in | Local only: backend not running on `:8000` — restart terminal |
| Behavioral Profile shows "Building your profile" | Click Simulate Week again |
| Simulate Week button not visible | Logged in as non-demo tenant — sign out, sign in as `demo` |
| Response takes > 30 seconds | Gemini rate limit — wait 60 seconds, retry |

---

## After the Demo

Click **Reset System** (top-right header) to wipe the database before the next run — or via curl:

```bash
# Live deploy
curl -X POST https://kinetic-api-drk6.onrender.com/api/debug/reset \
  -H "Authorization: Bearer <token>"

# Local
curl -X POST http://localhost:8000/api/debug/reset \
  -H "Authorization: Bearer <token>"
```
