# Kinetic — Presentation Reference

**Presenter:** Karl Johnson

Talking points for the Pursuit AI-Native L1 capstone review. Use alongside `DEMO.md`.

---

## Named User

**Jordan is a senior software engineer at a growth-stage startup.** He ships 50+ hours a week, runs a complex life, and has the discipline to instrument everything at work — CI pipelines, on-call runbooks, sprint boards — but runs his personal infrastructure completely on instinct. Sleep, home logistics, close relationships: no dashboards, no alerting, no triage list.

By the time he notices something is wrong, he's three weeks into a compounding debt spiral: sleep deficit driving cognitive decline, a domestic backlog that now requires a weekend to clear, and a close friend he hasn't spoken to in two weeks. The only feedback loop he had was burnout — and burnout doesn't fire until the damage is already done.

Kinetic gives Jordan the same observability layer for his personal systems that he already has for his production systems.

---

## Success Metric

**A user who checks in once per day for seven days will spend fewer than five minutes per day on triage, surface at least three high-leverage actions per week before they compound, and avoid at least one reactive recovery event — which typically costs 4–8 hours of lost flow time — per month.**

The ROI card operationalizes this: time recovered through outsourcing suggestions, margin reclaimed as a percentage, and projected burnout risk delta if the surfaced actions are resolved.

---

## Technology Choices + Rationale

**Gemini 2.5 Flash + Instructor** — Instructor wraps any LLM with Pydantic model enforcement, making structured extraction reliable rather than fragile. Without it, JSON parsing from raw LLM output breaks on edge cases constantly. Flash specifically targets sub-2-second parse latency, which matters at demo time. The orchestrator never touches raw text — it receives a fully validated, typed `CheckInPayload` every time.

**SQLite → PostgreSQL (dual-mode via `DatabaseClient` Protocol)** — SQLite for local dev: zero configuration, zero infrastructure, instant onboarding. PostgreSQL via asyncpg for production on Render: managed, scalable, persistent across deploys. The `DatabaseClient` Protocol means both backends satisfy the same 15-method interface; switching from SQLite to PostgreSQL requires zero application code changes. The dual-mode `get_db()` function in the orchestrator selects the backend at runtime based on whether `DATABASE_URL` is set.

**SSE streaming** — Chosen over WebSockets (no bidirectional requirement) and polling (unacceptable latency). The browser's native `EventSource` API was ruled out because it doesn't support POST bodies — the check-in message must travel in the request body, not query parameters. Instead, the frontend uses `fetch` + `ReadableStream` with manual SSE line parsing, which gives full control over event types (`agents`, `token`, `done`) and degrades gracefully to the non-streaming `/api/checkin` endpoint on any network failure.
