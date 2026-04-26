# Kinetic — Development Roadmap

**Project:** Bio-Operational Triage Engine
**Total timeline:** 10 days (2026-04-25 → 2026-05-05)
**Demo deadline:** Day 8 · 2026-05-03 — all agents working end-to-end
**MVP deadline:** Day 10 · 2026-05-05 — fully polished, stretch goals as time allows

> Sprints map to the PRD's four phases. Each sprint targets a version bump via
> `./scripts/release.sh`. The `/docs-keeper` agent updates this file at the end
> of every feature cycle.

---

## Legend

```
✅  Complete       🔄  In progress       ⬜  Not started       🔷  Stretch goal
```

---

## Sprint 0 — Bootstrap ✅
**Dates:** 2026-04-25 · **Version:** `v0.1.0` · **PRD ref:** pre-Phase 1

Foundation: professional tooling, typed skeletons, AI agent team, deployment config.

### Tooling & Config
- [x] `pyproject.toml` — uv, ruff, mypy strict, pytest, commitizen
- [x] `.pre-commit-config.yaml` — ruff, mypy, prettier, conventional-pre-commit
- [x] `CLAUDE.md` + `GEMINI.md` — full project docs + OS auto-detect startup ritual
- [x] `.claude/settings.json` — pre-approved commands
- ~~`render.yaml` — Render Blueprint~~ (removed; MVP demos locally)
- [x] `scripts/release.sh` — SemVer release ceremony
- [x] `.env.example` — environment variable template
- [x] `CHANGELOG.md` — Keep-a-Changelog initialized

### Python Skeleton
- [x] Pydantic v2 input models (`CheckInPayload`, `BioInput`, `LogisticsInput`, `RelationalInput`)
- [x] Pydantic v2 output models (`SystemHealthPayload`, `BioStatus`, `LogisticsStatus`, `RelationalStatus`, `TriageItem`, `ROISummary`)
- [x] `Agent` Protocol base class + `AgentResult`
- [x] Typed agent stubs: `BioArchivist`, `LogisticsFixer`, `RelationalDiplomat`
- [x] Lead orchestrator skeleton (routing logic, status aggregation)
- [x] LLM parser stub (Gemini + Instructor integration point)
- [x] FastAPI app skeleton (`GET /health`, `POST /api/checkin`)
- [x] 8 passing unit tests on model layer (100% model coverage)

### React Skeleton
- [x] Vite + TypeScript strict, path aliases
- [x] Vitest + `@testing-library/react` + jsdom
- [x] Playwright + `@axe-core/playwright` e2e scaffold
- [x] ESLint flat config (TypeScript-ESLint + `jsx-a11y` strict + Prettier)
- [x] `frontend/src/types/index.ts` — TypeScript interfaces mirroring Python models
- [x] Split-panel `App.tsx` shell + 3 passing component tests
- [x] Production build verified

### Agent Team
- [x] `/architect` slash command
- [x] `/backend-dev` slash command
- [x] `/frontend-dev` slash command
- [x] `/qa-reviewer` slash command
- [x] `/security-reviewer` slash command
- [x] `/docs-keeper` slash command

---

## Sprint 1 — Agent Logic ✅
**Dates:** 2026-04-26 → 2026-04-27 · **Target version:** `v0.2.0` · **PRD ref:** Phase 1 + Phase 2 (partial)

Implement real business logic in all three agents and the lead orchestrator. All stubs graduate to working implementations with ≥80% test coverage.

### BioArchivist
- [x] Burnout score algorithm (weighted average of sleep debt, nutrition quality, energy trend)
- [x] Sleep debt calculation (rolling 7-day vs. 8h baseline)
- [x] Burnout forecast string (green/yellow/red thresholds with plain-language explanation)
- [x] `BioArchivistResult` → `BioStatus` fully populated
- [x] Unit tests: happy path, partial input (sleep only), no input guard

### LogisticsFixer
- [x] Criticality threshold logic (`days_overdue` × `priority` weight → `StatusLevel`)
- [x] `critical_tasks` list (tasks that cross the red threshold)
- [x] Outsourcing suggestion stubs (static demo responses keyed by task name)
- [x] `time_to_resolve_minutes` estimation
- [x] `LogisticsFixerResult` → `LogisticsStatus` fully populated
- [x] Unit tests: all-green tasks, one critical task, multiple critical tasks

### RelationalDiplomat
- [x] Connection margin score (weighted average of vibe check scores vs. days-since-contact decay)
- [x] At-risk relationship detection (`score < 5` OR `days_since_contact > 7`)
- [x] Interaction sprint suggestions (templated by relationship type)
- [x] `RelationalDiplomatResult` → `RelationalStatus` fully populated
- [x] Unit tests: all healthy, one at-risk, all at-risk

### Lead Orchestrator
- [x] Full routing with graceful agent failure handling (agent raises → `overall_status` degrades, others still run)
- [x] `overall_status` aggregation: worst-case across fired agents
- [x] `triage_items` compilation from all agent outputs (sorted by priority descending)
- [x] Unit tests: all agents fire, partial payload (bio only, relational only), all agents fail

### Quality Gates
- [x] `uv run pytest` passes — 35 tests, 88% coverage
- [x] `uv run mypy src/kinetic --strict` → 0 errors
- [x] `uv run ruff check src/ tests/` → 0 warnings
- [x] `/qa-reviewer` approval — 35 tests, 88% coverage, all critical paths covered
- [x] `/security-reviewer` approval — bandit clean, no high/critical npm vulns, CORS dev-scoped (production config deferred to Sprint 2)
- [x] `/docs-keeper` updates ROADMAP.md, CHANGELOG.md

---

## Sprint 2 — LLM Parsing Layer ✅
**Dates:** 2026-04-28 → 2026-04-29 · **Target version:** `v0.3.0` · **PRD ref:** Phase 2 (completion)

Wire Gemini 2.5 Flash + Instructor into the parsing layer. `POST /api/checkin` goes end-to-end.

### LLM Parser
- [x] `parse_checkin()` — Gemini 2.5 Flash call via Instructor, returns typed `CheckInPayload`
- [x] Prompt engineering: system prompt instructs structured extraction of bio/logistics/relational fields
- [x] Graceful handling: partial messages (only bio mentioned) → correct sub-model population
- [x] `GEMINI_API_KEY` environment guard (clear error if missing)
- [x] Unit test (mocked Gemini): verify `CheckInPayload` structure from example messages
- [x] Integration test (live call, marked `@pytest.mark.integration`): verify round-trip from freetext

### FastAPI Route
- [x] `POST /api/checkin` fully wired: body → `parse_checkin()` → `orchestrate()` → `SystemHealthPayload`
- [x] Input validation: empty message → `400`
- [x] Agent failure → `500` with non-leaking error message
- [x] Integration tests via `httpx.AsyncClient` (TestClient)

### Quality Gates
- [x] All Sprint 1 gates still passing
- [x] Integration test suite passes (with `GEMINI_API_KEY` set)
- [x] Manual smoke test: `curl -X POST localhost:8000/api/checkin -d '{"message": "..."}'` returns valid JSON
- [x] `/qa-reviewer` + `/security-reviewer` + `/docs-keeper` approvals

---

## Sprint 3 — Frontend Core ✅
**Dates:** 2026-04-30 → 2026-05-01 · **Target version:** `v0.4.0` · **PRD ref:** Phase 3 (partial)

Build the split-panel UI: ChatPanel for input, Dashboard for live agent output.

### API Client
- [x] `src/api/client.ts` — typed `fetchCheckin(message: string): Promise<SystemHealthPayload>`
- [x] Handles `VITE_API_BASE_URL` for production (Render) vs. Vite proxy (dev)
- [x] Unit tests: success response, 400 error, 500 error

### ChatPanel Component
- [x] Message input (textarea + submit button)
- [x] Suggested prompt chips (3 example messages for first-time UX)
- [x] Message history display (user messages + Kinetic responses)
- [x] Loading state (spinner / "Analyzing..." indicator)
- [x] Empty state: "Brief your system. What's your status?"
- [x] Vitest: renders, submit triggers API call, loading state shown, error state shown
- [x] Playwright: type message → submit → response appears (with mocked API)

### Dashboard Component
- [x] `OverallStatusBadge` — green/yellow/red with text label + ARIA role
- [x] `BioStatusCard` — burnout score, forecast, recommendations list
- [x] `LogisticsStatusCard` — critical tasks, outsourcing suggestions
- [x] `RelationalStatusCard` — connection margin, at-risk relationships, sprints
- [x] Empty/default state: "You're all green!" (or per-card: "No data yet")
- [x] Vitest: renders each card in all three status levels + empty state

### TriageList Component
- [x] Flat list of `TriageItem`s sorted by priority
- [x] Each item: priority badge, domain tag, description, action CTA
- [x] Mark complete / snooze actions (local state for demo)
- [x] Empty state: "No actions needed. Nice work."
- [x] Vitest: renders items, complete action removes item, empty state shown

### Quality Gates
- [x] `npm run test:coverage` → ≥80% all thresholds
- [x] `npm run lint` → 0 errors (including jsx-a11y)
- [x] `npm run typecheck` → 0 errors
- [x] Playwright e2e + axe audit → 0 WCAG 2.1 AA violations
- [x] `/qa-reviewer` + `/security-reviewer` + `/docs-keeper` approvals

---

## Sprint 4 — Integration, ROI & Liaison ✅
**Dates:** 2026-05-02 → 2026-05-03 · **Target version:** `v0.5.0` · **PRD ref:** Phase 3 (completion)

Full frontend–backend integration, streaming responses, ROI calculator, and the Operational Liaison accessibility layer. **Demo-ready by end of sprint.**

### Full Integration
- [x] `App.tsx` wired: ChatPanel submit → `fetchCheckin()` → Dashboard updates
- [x] Loading states propagate from API call to all Dashboard cards
- [x] Error states: agent failure surfaces as degraded card (not blank crash)
- [x] Status lights animate on update (CSS transition, not JS)

### ROI Calculator
- [x] `ROISummaryCard` component — `time_recovered_minutes`, `margin_recovered`, `burnout_risk_delta`
- [x] Backend: `roi_summary` field populated by orchestrator once ≥1 domain has data
- [x] Empty state: `null` `roi_summary` renders "Insufficient data for ROI calculation" (non-alarming)
- [x] Vitest + Playwright coverage

### Operational Liaison (Executive Function Accessibility)
- [x] `OperationalLiaison` agent: provides clinical & tactical micro-tasking to break decision paralysis
- [x] Orchestration: runs after other agents to translate findings into tactical scripts
- [x] System prompt engineering: NOC-style tone, cognitive load reduction, task-dropping authority
- [x] Unit tests: verify tactical response structure based on aggregated triage items

### Conversational Dialogue UI
- [x] `ChatPanel` evolution: from static input to scrolling dialogue feed
- [x] State management: persist message history in the frontend session (and hydrate from DB)
- [x] System message rendering: distinct styling for tactical [SYSTEM] readouts
- [x] Suggested prompts: update to trigger specific paralysis-breaking scenarios

### End-to-End Demo Flow
- [x] Persistence: Pivot from LadybugDB to SQLite for stability on Windows.
- [x] Hydration: Page refresh preserves dashboard state and dialogue history.
- [x] Playwright e2e: full check-in message → all three agent cards update → triage list populates
- [x] Axe audit on fully-populated dashboard state (not just empty shell)

### Quality Gates
- [x] All prior sprint gates still passing
- [x] Playwright e2e full demo flow passes
- [x] Manual demo run: verify narrative from PRD ("Slept 5 hours, ate okay, feeling disconnected from Marcus")
- [x] `/qa-reviewer` + `/security-reviewer` + `/docs-keeper` approvals

> **Critical milestone: demo-ready prototype by 2026-05-03 (Day 8)**

---

## Sprint 5 — Behavioral Memory ✅
**Dates:** 2026-04-26 → 2026-04-30 · **Target version:** `v0.6.0` · **PRD ref:** Phase 3+

Persistent, accumulating behavioral understanding of the user. The app gets to know patterns over time and uses them to ground the OperationalLiaison's tactical guidance.

### Data Layer (backend)
- [x] New Pydantic output models: `BioTrend`, `RecurringTask`, `RelationalDrift`, `BehavioralSummary`, `BehavioralProfile`
- [x] `behavioral_profiles` table added to SQLite schema (idempotent migration in `_init_db()`)
- [x] `SqliteClient.get_behavioral_summary(days: int = 14) -> BehavioralSummary` — queries 7–14 days of bio_metrics, checkin_tasks, vibe_checks; computes sleep slope via `statistics.linear_regression`, recurring task detection, relational drift velocity
- [x] `SqliteClient.get_behavioral_profiles() -> list[BehavioralProfile]`
- [x] `SqliteClient.upsert_behavioral_profile(profile: BehavioralProfile) -> None`
- [x] `SystemHealthPayload` gains field: `behavioral_profiles: list[BehavioralProfile]`
- [x] `frontend/src/types/index.ts` updated to mirror all new models

### Pattern Detector Service (backend)
- [x] New file: `src/kinetic/services/pattern_detector.py`
- [x] `detect_and_update_patterns(db, behavioral_summary, current_profiles, api_key) -> None`
- [x] Rate-limit guard: no-op if `days_analyzed < 3` or any profile updated within 20 hours
- [x] Gemini call to derive behavioral patterns from summary; upserts profiles via db
- [x] All exceptions caught and logged — never propagates (background task safety)

### Orchestrator + Liaison Integration (backend)
- [x] `orchestrate()` calls `get_behavioral_summary()` and `get_behavioral_profiles()` after agents fire
- [x] `OperationalLiaison.process()` signature updated to accept `behavioral_summary` and `behavioral_profiles`
- [x] System prompt gains BEHAVIORAL CONTEXT section and 14-day trend summary
- [x] `asyncio.create_task(detect_and_update_patterns(...))` fires non-blocking after Liaison responds
- [x] All existing orchestrator tests still pass

### Frontend — Behavioral Profile Panel (stretch)
- [x] `BehavioralProfilePanel` component (collapsible disclosure, keyboard-navigable)
- [x] Empty state: "Building your profile — check in again tomorrow."
- [x] Vitest + Playwright + axe coverage

### Quality Gates
- [x] All prior sprint gates still passing
- [x] `uv run pytest --cov-fail-under=80` passes
- [x] `uv run mypy src/kinetic --strict` → 0 errors
- [x] `npm run typecheck` → 0 errors
- [x] `/qa-reviewer` + `/security-reviewer` + `/docs-keeper` approvals

---

## Sprint 6 — Polish & Demo Prep 🔄
**Dates:** 2026-05-01 → 2026-05-05 · **Target version:** `v1.0.0` · **PRD ref:** Phase 4

Error handling, empty states, accessibility, demo script.

### Error & Empty States
- [x] Agent failure fallback: degraded status card with "Agent unavailable" message + retry CTA
- [x] Malformed input: `400` response surfaced as inline error (not toast, not crash)
- [x] Missing `GEMINI_API_KEY`: clear startup warning in logs, API returns `503` with helpful message
- [x] All empty states reviewed for non-alarming, non-judgmental copy

### Onboarding Flow
- [ ] 3-screen micro-tutorial (skippable): "Personal infrastructure", "Chat-first", "Agent roles"
- [ ] First-time detection: `localStorage` flag, shown once
- [ ] Vitest + Playwright: tutorial renders, skip works, doesn't re-appear on reload

### Accessibility Final Audit
- [ ] Full axe WCAG 2.1 AA audit on: empty state, loaded state, error state, onboarding
- [ ] Keyboard navigation: all interactive elements reachable and operable without mouse
- [ ] Color contrast: all status colors meet 4.5:1 ratio (green/yellow/red on dark bg)
- [ ] Screen reader smoke test: status cards announce meaningful content

### Demo Preparation
- [ ] Demo script written (step-by-step walkthrough of PRD narrative)
- [ ] Seeded demo state available (pre-populated check-in data for live demo)
- [ ] Local demo run verified end-to-end: backend on :8000, frontend on :5173, full check-in flow

### Stretch Goals 🔷
- [ ] Persistent historical state (file-based storage, SQLite, or localStorage)
- ~~**LadybugDB Integration:** Implement embedded Graph+Vector memory for long-term accountability and pattern detection.~~ (superseded by Behavioral Memory — Sprint 5, which achieves the same goal via SQLite + Gemini pattern synthesis)
- [x] ~~**Behavioral Profile Panel** (if not completed in Sprint 5)~~ (completed in Sprint 5)
- [ ] Burnout trend chart (7-day sparkline)
- [ ] Agent log / history panel (collapsible sidebar)
- [ ] Basic auth for stretch MVP (single hardcoded credential, no multi-user)

### Quality Gates
- [ ] All prior sprint gates still passing
- [ ] `v1.0.0` release ceremony complete (`./scripts/release.sh`)
- [ ] Local demo run rehearsed end-to-end

> **Critical milestone: fully functional MVP by 2026-05-05 (Day 10)**

---

## Architectural Decision: Behavioral Memory via SQLite

**Decision (2026-04-25):** LadybugDB (embedded Graph+Vector DB) was attempted and abandoned due to native binary incompatibility on Windows. The same goal — the app accumulating knowledge of the user's behavioral patterns over time — is achieved via:

1. **SQLite time-series queries** for 7–14 day trend computation (sleep slope, recurring task detection, relational drift velocity)
2. **`behavioral_profiles` table** for Gemini-derived insights that persist and accumulate across check-ins
3. **`OperationalLiaison` context injection** so pattern awareness directly informs tactical guidance

The data is time-series shaped, not graph-shaped. SQLite handles all required queries cleanly without additional dependencies.

---

## Version Map

| Version | Sprint | PRD Phase | Status |
|---------|--------|-----------|--------|
| `v0.1.0` | Sprint 0 — Bootstrap | Pre-Phase 1 | ✅ Released |
| `v0.2.0` | Sprint 1 — Agent Logic | Phase 1 + Phase 2 partial | ✅ Released |
| `v0.3.0` | Sprint 2 — LLM Parsing | Phase 2 complete | ✅ |
| `v0.4.0` | Sprint 3 — Frontend Core | Phase 3 partial | ✅ |
| `v0.5.0` | Sprint 4 — Integration | Phase 3 complete | ✅ |
| `v0.6.0` | Sprint 5 — Behavioral Memory | Phase 3+ | ✅ |
| `v1.0.0` | Sprint 6 — Polish + Demo | Phase 4 | ⬜ |
