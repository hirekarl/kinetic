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
- ~~`render.yaml` — Render Blueprint~~ (removed; MVP demos locally; restored Sprint 9)
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

## Sprint 6 — Polish & Demo Prep ✅
**Dates:** 2026-05-01 → 2026-05-05 · **Target version:** `v1.0.0` · **PRD ref:** Phase 4

Error handling, empty states, accessibility, demo script.

### Error & Empty States
- [x] Agent failure fallback: degraded status card with "Agent unavailable" message + retry CTA
- [x] Malformed input: `400` response surfaced as inline error (not toast, not crash)
- [x] Missing `GEMINI_API_KEY`: clear startup warning in logs, API returns `503` with helpful message
- [x] All empty states reviewed for non-alarming, non-judgmental copy

### Onboarding Flow
- [x] 3-screen micro-tutorial (skippable): "Personal infrastructure", "Chat-first", "Agent roles"
- [x] First-time detection: `localStorage` flag, shown once
- [x] Vitest + Playwright: tutorial renders, skip works, doesn't re-appear on reload

### Accessibility Final Audit
- [x] Full axe WCAG 2.1 AA audit on: empty state, loaded state, error state, onboarding
- [x] Keyboard navigation: all interactive elements reachable and operable without mouse
- [x] Color contrast: all status colors meet 4.5:1 ratio (green/yellow/red on dark bg)
- [x] Screen reader smoke test: status cards announce meaningful content

### Demo Preparation
- [x] Demo script written (step-by-step walkthrough of PRD narrative)
- [x] Seeded demo state available (pre-populated check-in data for live demo)
- [x] Local demo run verified end-to-end: backend on :8000, frontend on :5173, full check-in flow

### Stretch Goals 🔷
- [ ] Persistent historical state (file-based storage, SQLite, or localStorage)
- ~~**LadybugDB Integration:** Implement embedded Graph+Vector memory for long-term accountability and pattern detection.~~ (superseded by Behavioral Memory — Sprint 5, which achieves the same goal via SQLite + Gemini pattern synthesis)
- [x] ~~**Behavioral Profile Panel** (if not completed in Sprint 5)~~ (completed in Sprint 5)
- [x] Burnout trend chart (7-day sparkline)
- [ ] Agent log / history panel (collapsible sidebar)
- [ ] Basic auth for stretch MVP (single hardcoded credential, no multi-user)

### Quality Gates
- [x] All prior sprint gates still passing
- [x] `v1.0.0` release ceremony complete (`./scripts/release.sh`)
- [x] Local demo run rehearsed end-to-end

> **Critical milestone: fully functional MVP by 2026-05-05 (Day 10)**

---

## Sprint 6b — Dashboard Interactivity + Liaison Hardening ✅
**Dates:** 2026-04-26 → TBD · **Target version:** `v1.1.0`

Conversational depth, specialist agent routing, contact pause lifecycle, task completion UI, and adversarial scenario coverage.

### Implemented (2026-04-26)
- [x] Conversational history threading: `history` forwarded `routes.py` → `orchestrate()` → `OperationalLiaison.process()`; LLM receives prior turns capped at 10
- [x] Specialist routing: `LiaisonResponse.responding_agent` field; liaison routes to `bio_archivist`, `logistics_fixer`, `relational_diplomat`, or `liaison`; ChatPanel renders colored agent label per message
- [x] Rich specialist context: orchestrator passes `bio_status`, `logistics_status`, `relational_status` to liaison so it grounds responses in live data
- [x] Contact pause lifecycle: `ContactPauseDirective` extracted by liaison → persisted to `contact_pauses` SQLite table → active pauses filter triage items + relational status + interaction sprints
- [x] `ContactPause` model added to `SystemHealthPayload.active_pauses`; Relational Diplomat card shows "On Break" section

### Task A1 — Server-Persisted Task Completion (backend) ✅
- [x] `source_id: str | None = None` on `TriageItem`
- [x] `LogisticsFixer` sets `source_id=task.name` on generated triage items
- [x] `SqliteClient.complete_task(task_name: str) -> None`
- [x] `LiaisonResponse.task_completions: list[str]` field
- [x] Orchestrator iterates `task_completions`, calls `db.complete_task()` for each
- [x] `PATCH /api/tasks/{task_name}/complete` endpoint (200 | 404 | 409)
- [x] TS type: `TriageItem.source_id: string | null`

### Task A2 — Triage Completion UI (frontend) ✅
- [x] Checkmark button on logistics triage items with non-null `source_id`
- [x] Optimistic removal on click; restore on API error
- [x] `TriageList` accepts `onCompleteTask?: (taskName: string) => Promise<void>`
- [x] `App.tsx` `handleCompleteTask` wired up
- [x] WCAG 2.1 AA compliance on new interactive elements

### Task B1 — Liaison Prompt Hardening (backend) ✅
- [x] SYNTHESIS rule: competing multi-domain crisis → unified sequenced protocol
- [x] IMPROVEMENT ACK rule: partial recovery → acknowledge delta, update forecast
- [x] EVENT ROUTING rule: upcoming deadline → one action per specialist domain
- [x] HISTORY RESOLUTION rule: pronoun references → resolve from last 3 turns
- [x] AGENCY rule: user overrides recommendation → pivot to risk mitigation only
- [x] Orchestrator processes `task_completions` directive (same pattern as contact pauses)

### Task B2 — Scenario Test Suite + Live Runner (both) ✅
- [x] `tests/scenarios/test_scenarios.py` — 5 deterministic mocked scenario fixtures
- [x] `scripts/run_scenarios.py` — live runner against `:8000`

### Quality Gates
- [x] All prior sprint gates still passing (86% backend coverage, 124 frontend tests)
- [x] `v1.1.0` release ceremony complete

---

## Architectural Decision: Behavioral Memory via SQLite

**Decision (2026-04-25):** LadybugDB (embedded Graph+Vector DB) was attempted and abandoned due to native binary incompatibility on Windows. The same goal — the app accumulating knowledge of the user's behavioral patterns over time — is achieved via:

1. **SQLite time-series queries** for 7–14 day trend computation (sleep slope, recurring task detection, relational drift velocity)
2. **`behavioral_profiles` table** for Gemini-derived insights that persist and accumulate across check-ins
3. **`OperationalLiaison` context injection** so pattern awareness directly informs tactical guidance

The data is time-series shaped, not graph-shaped. SQLite handles all required queries cleanly without additional dependencies.

---

## Sprint 7 — Agent Dispatch Log ✅
**Dates:** 2026-04-26 → TBD · **Target version:** `v1.2.0`

Make the multi-agent routing visible during a live demo via a collapsible Agent Dispatch Log panel in the Mission Control dashboard. Pure frontend feature — no backend or model changes.

### Tasks
- [x] `AgentFired` + `AgentLogEntry` types added to `frontend/src/types/index.ts`
- [x] `buildAgentLogEntry` utility at `frontend/src/utils/agentLog.ts`
- [x] `AgentDispatchLog` component at `frontend/src/components/Dashboard/AgentDispatchLog.tsx`
      — collapsible, newest-first, per-entry expandable agent summaries + responding_agent badge
- [x] `App.tsx` accumulates `agentLog: AgentLogEntry[]` state; passes to `AgentDispatchLog`
- [x] Vitest: empty state, full entry, partial entry, expand/collapse, `buildAgentLogEntry` util (21 new tests; 145 total passing)
- [x] Playwright e2e + axe: 51/51 across Chromium, Firefox, mobile Safari — zero WCAG 2.1 AA violations

### Quality Gates
- [x] All prior sprint gates still passing (145 tests, 95.4% coverage)
- [x] `npm run typecheck` → 0 errors
- [x] `npm run lint` → 0 errors (including jsx-a11y)
- [x] Frontend coverage ≥ 80% on new files (`AgentDispatchLog.tsx` 100%, `agentLog.ts` 100%)
- [x] `v1.2.0` release ceremony complete

---

## Sprint 8 — Multi-Tenant Authentication ✅
**Dates:** 2026-04-26 → TBD · **Target version:** `v1.3.0`

Per-tenant data isolation, JWT-based sessions, and a frontend login screen. Two tenants: `demo` and `personal`.

### Task A — Auth Backend ✅
- [x] `src/kinetic/auth.py` — TenantConfig, CurrentUser models; load_credentials(), verify_password(), create_access_token(), decode_access_token(), get_current_user(), get_current_tenant() FastAPI dependencies
- [x] `src/kinetic/api/auth.py` — POST /api/auth/login, GET /api/auth/me, POST /api/auth/logout
- [x] All four API routes protected with get_current_tenant() dependency
- [x] Per-tenant SQLite DB isolation: get_db(tenant) → kinetic_{tenant}.db; module-level _db_clients dict cache
- [x] credentials.toml.example committed; credentials.toml gitignored
- [x] SECRET_KEY startup warning in main.py; SECRET_KEY + CREDENTIALS_PATH added to .env.example
- [x] PyJWT ≥ 2.8 + bcrypt ≥ 4.0 dependencies added (passlib removed — incompatible with bcrypt 5.x)
- [x] 26 new tests: unit/test_auth.py (12), unit/test_lead_db.py (3), integration/test_auth_routes.py (11)
- [x] 158/158 tests passing, 87% coverage, mypy strict ✓, ruff ✓

### Task B — Auth Frontend ✅
- [x] `AuthUser` type added to `frontend/src/types/index.ts`
- [x] `useAuth` hook: login(), logout(), fetchMe(), token storage in localStorage
- [x] `LoginScreen` component: username + password form, error state, loading state
- [x] `App.tsx` gate: show LoginScreen if unauthenticated; persist session token
- [x] All API client calls pass Bearer token in Authorization header
- [x] Playwright e2e: login → dashboard → logout → login screen shown again
- [x] 174/174 unit tests passing, 95.78% coverage; 66/66 Playwright tests (zero WCAG 2.1 AA violations)

### Quality Gates
- [x] All prior sprint gates still passing
- [x] `v1.3.0` release ceremony complete

---

## Sprint 9 — PostgreSQL Migration ✅
**Dates:** 2026-04-27 · **Target version:** `v1.4.0`

Migrate the database layer from per-tenant SQLite files to Render's managed PostgreSQL (basic-256mb). Introduces a `DatabaseClient` Protocol so both backends satisfy the same interface; local dev continues to use SQLite with zero change. Multi-tenancy moves from separate DB files to a `tenant` column on every table.

### Infrastructure (completed)
- [x] `render.yaml` — Render Blueprint: Python API service + static frontend + PostgreSQL database (basic-256mb); `SECRET_KEY` auto-generated; `GEMINI_API_KEY` + `FRONTEND_URL` + `VITE_API_BASE_URL` marked `sync: false`
- [x] `.python-version` — pins Python 3.12 for uv and Render
- [x] `src/kinetic/main.py` — CORS `allow_origins` now reads `FRONTEND_URL` env var at startup (production Render URL)

### Task 1 — DatabaseClient Protocol ✅
- [x] `src/kinetic/db/base.py` — `DatabaseClient` Protocol with all 13 method signatures
- [x] `orchestrator/lead.py` — `get_db()` return type + `_db_clients` dict typed as `DatabaseClient`; `orchestrate()` `db` param typed as `DatabaseClient | None`
- [x] `services/pattern_detector.py` — `db` param type updated from `SqliteClient` to `DatabaseClient`
- [x] `mypy --strict` passes; no behavior change

### Task 2 — PostgresClient implementation ✅
- [x] `src/kinetic/db/postgres_client.py` — asyncpg-backed `PostgresClient` satisfying `DatabaseClient` Protocol
- [x] `_migrate()` — idempotent DDL: all 7 tables with `tenant TEXT NOT NULL`; `inserted_at TIMESTAMPTZ DEFAULT NOW()` on `bio_metrics`, `vibe_checks`, `checkin_tasks`; composite unique constraints for tenant-scoped natural keys
- [x] All 13 public methods ported: `?` → `$N` params, SQLite date arithmetic → Python-computed cutoffs, `rowid` ordering → `inserted_at DESC`, `clear_database()` deletes only `WHERE tenant = $1`
- [x] `uv add asyncpg>=0.31.0` (runtime dep added to `pyproject.toml`)
- [x] `tests/integration/test_postgres_client.py` — 29 tests covering all 13 methods + tenant isolation; guarded by `@pytest.mark.skipif(not DATABASE_URL)`

### Task 3 — Pool lifecycle + dual-mode `get_db()` ✅
- [x] `main.py` lifespan — creates `asyncpg.Pool` (min=2, max=10) when `DATABASE_URL` set; calls `_migrate()` once; closes pool on shutdown; logs info when absent (SQLite fallback)
- [x] `orchestrator/lead.py` — `_pg_pool: asyncpg.Pool | None = None` module-level var; `get_db()` returns `PostgresClient(pool, tenant)` when pool live; `SqliteClient` otherwise
- [x] Unit tests: 3 pool-branch tests in `test_lead_db.py`; 2 lifespan pool tests in `test_main.py` (AsyncMock, no real DB required)

### Quality Gates
- [x] All prior sprint gates still passing (180 passed, 29 skipped — PostgreSQL integration tests without DATABASE_URL)
- [x] `uv run pytest --cov-fail-under=80` passes — 81% aggregate coverage
- [x] `uv run mypy src/kinetic --strict` → 0 errors
- [x] `/qa-reviewer` approval — APPROVED
- [x] `/security-reviewer` approval — APPROVED (bandit 0 issues; pip-audit 1 informational; npm audit 6 moderate dev-only)
- [x] `/docs-keeper` updates complete
- [x] `v1.4.0` release ceremony complete

---

## Sprint 10 — Streaming Responses ✅
**Dates:** TBD · **Target version:** `v1.5.0`

Stream the Operational Liaison's reply token-by-token via Server-Sent Events. The dashboard updates the moment the first token arrives, eliminating the dead pause during a live demo.

### Backend ✅
- [x] Add `sse-starlette` dependency (`uv add sse-starlette`)
- [x] New endpoint `POST /api/checkin/stream` — SSE variant of `/api/checkin`; requires `get_current_tenant`
- [x] Emit `event: agents` first — full `SystemHealthPayload` with agent status cards (no liaison text yet); frontend can render cards immediately
- [x] Stream Liaison reply via `generate_content_stream` (google-genai streaming API); emit `event: token` per chunk
- [x] Emit `event: done` with final `responding_agent` + `contact_pauses` + `task_completions` metadata
- [x] Unit tests: SSE event sequence, agent-event shape, done-event shape, agent failure recovery, contact pause + task completion side effects (17 tests)
- [x] Integration tests: full SSE round-trip with mocked stream (6 tests)
- [x] `/qa-reviewer` approval — APPROVED (203 passed, 81% coverage, mypy ✓, ruff ✓)
- [x] `/security-reviewer` approval — APPROVED (no new vulnerabilities; sse-starlette clean)

### Frontend ✅
- [x] `streamCheckin()` in `client.ts` — `fetch` + `ReadableStream` with manual SSE line parsing; `fetchCheckin` fallback on non-200 or network error
- [x] `ContactPauseDirective` + `StreamDonePayload` types added to `frontend/src/types/index.ts`
- [x] `ChatPanel`: `streamingContent` prop drives in-progress bubble with blinking CSS cursor; replaced by finalized message on `done`
- [x] `App.tsx`: `streamCheckin` wired with `accumulatedRef` + `streamingContent` state; `onAgents` updates dashboard immediately; `onToken` appends text; `onDone` finalizes message
- [x] Pre-existing `useAuth.test.ts` localStorage bug fixed (Map-backed `vi.stubGlobal`)
- [x] Vitest: 185 tests passed (7 new streamCheckin + 4 new ChatPanel streaming); coverage 96%
- [x] ESLint (jsx-a11y): 0 errors; TypeScript: 0 errors

### Quality Gates
- [x] `uv run pytest` passes — 203 passed, 29 skipped, 0 failed
- [x] `uv run mypy src/kinetic --strict` → 0 errors
- [x] `npm run test:coverage` — 185 passed, 96% coverage
- [x] `npm run lint` → 0 errors
- [x] `npm run typecheck` → 0 errors
- [x] `/qa-reviewer` + `/security-reviewer` + `/docs-keeper` approvals (frontend)
- [x] `v1.5.0` release ceremony complete

---

## Sprint 11 — Burnout Trend Chart ✅
**Target version:** `v1.6.0`

Surface the 14-day burnout score history as a line chart in the Bio card. The data already exists in `bio_metrics`; this is purely a visualization sprint — no new backend data model required.

### Backend ✅
- [x] New method `SqliteClient.get_burnout_series(days: int = 14) -> list[float]` — ordered oldest→newest; per-entry burnout computed from stored bio_metrics via `_compute_burnout_scalar`
- [x] Mirror in `PostgresClient.get_burnout_series()` (ordered by `inserted_at ASC`)
- [x] Add `get_burnout_series` to `DatabaseClient` Protocol (`base.py`) — protocol now has 14 methods
- [x] `BioTrend.burnout_series: list[float]` field added to `src/kinetic/models/outputs.py`
- [x] `get_behavioral_summary()` wired in both clients — burnout_series computed inline from bio_rows (same query window as sleep_series, no second DB round-trip)
- [x] Unit tests: empty series, single entry, formula correctness, ordering, days-filter, partial data, all-None, perfect health; Postgres mock tests; summary wiring (14 tests total)
- [x] `/qa-reviewer` APPROVED (217 passed, 83% coverage, mypy ✓, ruff ✓)
- [x] `/security-reviewer` APPROVED (no new vulnerabilities; f-string offset is bind-param safe)

### Frontend ✅
- [x] `BurnoutTrendChart` component — SVG polyline matching `SleepSparkline` visual language; red/amber/emerald stroke from trend direction; `aria-hidden` with adjacent screen-reader text
- [x] `BioTrend` TS interface gains `burnout_series: number[]` in `frontend/src/types/index.ts`
- [x] Render below burnout score in `BioStatusCard`; null/hidden for < 2 data points
- [x] Vitest: 206 tests passing (16 new `BurnoutTrendChart` + 5 new `BioStatusCard`); 96% coverage
- [x] Playwright + axe: 66/66 passing, zero WCAG 2.1 AA violations
- [x] `/qa-reviewer` APPROVED (206 tests, 96% coverage, ESLint ✓, TypeScript ✓, axe ✓)
- [x] `/security-reviewer` APPROVED (pure presentational component; no new deps)

### Quality Gates
- [x] All prior gates passing
- [x] `v1.6.0` release ceremony complete

---

## Sprint 12 — Weekly Digest ✅
**Target version:** `v1.7.0`

A single Gemini call that ingests 14 days of bio/logistics/relational data and returns a prose "state of the system" paragraph. Shown as a collapsible "Weekly Review" card in the dashboard.

### Backend ✅
- [x] `DigestResponse(summary: str, generated_at: datetime)` added to `src/kinetic/models/outputs.py`
- [x] `src/kinetic/services/digest_generator.py` — `generate_digest()` with 6h in-memory cache per tenant; empty-history guard; Gemini raw `generate_content` call; exception-safe
- [x] `GET /api/digest?force=false` added to `routes.py`; 503 if GEMINI_API_KEY absent; requires `get_current_tenant`
- [x] Unit tests: happy path, cache hit/miss/TTL, `force=True` bypass+update, empty-data canned response, history-only guard bypass, Gemini exception recovery (10 tests)
- [x] Route tests: 200 shape, `force` forwarding, 401, 503 (5 tests)
- [x] CI hotfix: `get_burnout_series(days <= 0)` early return guards against SQLite datetime precision race on UTC CI runners
- [x] `/qa-reviewer` APPROVED (247 passed, 83% coverage, mypy ✓, ruff ✓)
- [x] `/security-reviewer` APPROVED (no new vulnerabilities; in-memory cache keyed by tenant string)

### Frontend ✅
- [x] `DigestResponse` TS interface added to `frontend/src/types/index.ts`
- [x] `fetchDigest(token?, force?)` added to `frontend/src/api/client.ts`; `force=true` appends `?force=true`
- [x] `WeeklyDigestCard` component — collapsible disclosure ("Weekly Review"); prose paragraph; "Generated X minutes ago" relative timestamp; Refresh button with spinner; loading skeleton; [DIGEST ERROR] error block; no-data empty state
- [x] `App.tsx`: `digestData`/`digestLoading`/`digestRefreshing` state; digest fetch alongside history in post-auth `useEffect`; `handleRefreshDigest` callback
- [x] Vitest: 14 tests — loading, populated (open/closed), no-data, error, refresh trigger, relative timestamp (220 total passing, 95% coverage)
- [x] Playwright + axe: 66/66 passing, zero WCAG 2.1 AA violations
- [x] `/qa-reviewer` APPROVED (220 tests, 95% coverage, ESLint ✓, TypeScript ✓, axe ✓)
- [x] `/security-reviewer` APPROVED (no new attack surfaces; digest text rendered as React text node)

### Quality Gates
- [x] All prior gates passing
- [x] `v1.7.0` release ceremony complete

---

## Sprint 13 — Demo Polish + Shareable Deploy ✅
**Target version:** `v1.8.0`

Six task groups targeting Demo Day (May 6, 2026): mobile responsiveness, Simulate Week feature, README, demo script structure, live Render deploy, and presentation documentation to close all rubric gaps.

### A — Mobile Responsive Layout
- [x] `App.tsx`: outer container `flex-col lg:flex-row`; chat panel `w-full lg:w-[420px] h-[45vh] lg:h-auto lg:shrink-0`; header `flex-wrap`; content padding `p-4 md:p-8`
- [x] `ChatPanel/index.tsx`: `border-r` → `border-b lg:border-b-0 lg:border-r`
- [x] Playwright smoke test at 375px viewport — zero layout overflow

### B — Simulate Week Feature
- [x] Backend: `POST /api/demo/simulate` — 403 guard for non-demo tenants; replays 5 pre-scripted check-ins with timestamps spread across 7 days, inserting bio metrics + tasks + vibe checks
- [x] Frontend: "Simulate Week" button visible only when `user.tenant === "demo"`; triggers endpoint then auto-refreshes digest + burnout trend chart
- [x] Unit tests: tenant guard (non-demo → 403), simulation inserts correct row count

### C — README.md
- [x] Stranger-runnable setup: env vars, `uv sync`, `npm install`, dev server commands, credentials setup
- [x] One-paragraph architecture summary
- [x] Local demo run instructions

### D — Demo Script Update (`docs/DEMO.md`) + Video Artifact
- [x] Complete rewrite of `docs/DEMO.md` as live in-person presentation script (Problem → Root Cause → Solution → Live Demo → What's Next); exact verbal lines + typed inputs for all 3 check-in turns; pre-demo setup checklist; troubleshooting table
- [x] `docs/NARRATION.md` — video voiceover script (~4 min) for Playwright-recorded video artifact; Jordan narrative arc, metric methodology explanations, [HOLD] markers
- [x] `frontend/e2e/live-demo.spec.ts` — 12-section Playwright demo recording script with mocked API, smooth scroll, mouse cursor overlay, simulated latency; all rubric requirements covered
- [x] `frontend/playwright-demo.config.ts` — dedicated Playwright config for demo video recording (headless, 1920×1080, 300s timeout)
- [x] Video artifact generated and verified at 1920×1080

### E — Render Deploy
- [x] `render.yaml` — `healthCheckPath: /health`, `preDeployCommand: uv run python scripts/migrate.py`, `plan: starter` (always-on)
- [x] `scripts/migrate.py` — standalone asyncpg pre-deploy DDL migration script
- [x] `docs/DEPLOY.md` — end-to-end deployment checklist with env vars, credentials setup, tenant lifecycle
- [x] Configure Render dashboard: `GEMINI_API_KEY`, `FRONTEND_URL`, `VITE_API_BASE_URL`, `credentials.toml` Secret File
- [x] Extend `scripts/seed_demo.py` to target PostgreSQL backend via `DATABASE_URL` (SQLite local + asyncpg Render modes)
- [x] Seed `demo` tenant on live PostgreSQL
- [x] Verify end-to-end on live Render URL: [https://kinetic-frontend-c2bd.onrender.com](https://kinetic-frontend-c2bd.onrender.com)
- [x] Update demo script with live URL

### F — Presentation Documentation
- [x] Sharpen named user one-liner (from "high-performance engineers" to a specific named persona with situation + frustration)
- [x] Write measurable success metric sentence
- [x] Technology choices + rationale paragraph (Gemini + Instructor, SQLite → PostgreSQL, SSE streaming)

### G — Landing Page + Brand Assets + SEO
- [x] Marketing landing page at `/` — nav, hero, domain cards, how-it-works, footer; `KineticLogo` inline SVG (three-line K convergence mark)
- [x] URL-based routing via react-router-dom: `/` landing, `/login` auth, `/app` dashboard; `useNavigate` post-login/logout redirects; `← Return to base` back-link on login screen
- [x] Brand asset generator `npm run brand` (Playwright-based PNG renderer): og-card (1200×630), twitter-card (1200×675), icon-512, icon-192, wordmark (900×200), landing-1920x1080 → `assets/brand/` + `frontend/public/`
- [x] SEO metadata in `index.html`: Open Graph, Twitter Card, JSON-LD structured data
- [x] PWA manifest (`site.webmanifest`): name, icons, theme color, display standalone
- [x] 7 Vitest tests for `LandingPage` component (hero, CTA, domain names, nav links, footer, eyebrow, how-it-works steps)

### Quality Gates
- [x] Mobile layout verified at 375px viewport (no overflow, all interactions reachable)
- [x] All prior gates passing (247 backend tests, 220 frontend tests)
- [x] Render deploy verified end-to-end with seeded demo tenant
- [x] `v1.8.0` release ceremony complete

---

## Sprint 14 — Structured Logging + SEO/LLM Discoverability ✅
**Target version:** `v1.9.0`

Replace ad-hoc `logging.getLogger` calls with a unified structlog pipeline. JSON output on Render; colorized human-readable output locally. Per-request context (tenant + request_id) bound automatically via middleware and auth dependency. Add web discoverability files and per-route meta tags.

### Backend ✅
- [x] `src/kinetic/logging_config.py` — `is_production()` + idempotent `setup_logging()`; structlog + stdlib bridge; `ConsoleRenderer` (dev) / `JSONRenderer` (prod); `cache_logger_on_first_use=False` for test compatibility
- [x] `src/kinetic/middleware/logging.py` — `StructlogRequestMiddleware`: per-request `clear_contextvars()` + `bind_contextvars(request_id, path, method)`; logs `request.start`, `request.done`, `request.error`
- [x] Auth callsites: `auth.login.success`, `auth.login.failure`, `auth.token.expired`, `auth.token.invalid`; `bind_contextvars(tenant=...)` in `get_current_user`
- [x] Orchestrator callsites: `agents.dispatch`, `agent.error` (with `agent=` field)
- [x] LLM callsites: `llm.parse.start/done`, `llm.call.start/done/error`, `llm.stream.start/done`, `llm.metadata.start/done`
- [x] Service callsites: `digest.cache.hit`, `digest.generate.start/done/error`, `pattern.detect.start/done/skipped/malformed_entry`
- [x] Startup callsites: `db.pool.created`, `db.sqlite.fallback`, `db.pool.closed`
- [x] `structlog>=24.0` added to `pyproject.toml` (installed as 25.5.0)
- [x] `tests/unit/test_logging_config.py` — 9 tests
- [x] `tests/unit/test_logging_middleware.py` — 8 tests
- [x] `/qa-reviewer` APPROVED (356 passed, 100% coverage, mypy ✓, ruff ✓)
- [x] `/security-reviewer` APPROVED (no new vulnerabilities; no sensitive data in log callsites)

### SEO / LLM Discoverability ✅
- [x] `frontend/public/llms.txt` — spec-compliant LLM discovery file (llmstxt.org): H1 + blockquote + App/Source/Optional sections
- [x] `frontend/public/robots.txt` — allows all crawlers; disallows `/app`; references sitemap
- [x] `frontend/public/sitemap.xml` — sitemaps.org/0.9: `/` (1.0) + `/login` (0.5)
- [x] `frontend/public/.well-known/security.txt` — RFC 9116: Contact + Expires + Preferred-Languages
- [x] `frontend/index.html` — canonical URL bug fixed (missing `-c2bd`); JSON-LD `@type` → `WebApplication`; `browserRequirements` + `featureList` added; `<link rel="sitemap">` in `<head>`
- [x] `react-helmet-async` installed; `<HelmetProvider>` wrapping app tree in `main.tsx`
- [x] Per-route `<Helmet>` added: LandingPage ("Kinetic — Bio-Operational Triage Engine"), LoginScreen ("Sign In — Kinetic"), dashboard ("Mission Control — Kinetic")
- [x] Test helpers updated with `HelmetProvider` wrappers; title assertion tests added (285 total, 100% coverage)
- [x] `Kinetic-PRD.md` moved from repo root to `docs/`

### Quality Gates
- [x] All prior gates passing (356 passed, 29 skipped, 0 failed)
- [x] `uv run mypy src/kinetic --strict` → 0 errors
- [x] `uv run ruff check src/ tests/` → 0 warnings
- [x] `npm run test:coverage` → 285 passed, 100% coverage
- [x] `npm run typecheck` → 0 errors
- [x] `npm run lint` → 0 errors
- [x] `v1.9.0` release ceremony complete

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
| `v1.0.0` | Sprint 6 — Polish + Demo | Phase 4 | ✅ Released |
| `v1.1.0` | Sprint 6b — Dashboard Interactivity + Liaison Hardening | Phase 4+ | ✅ |
| `v1.2.0` | Sprint 7 — Agent Dispatch Log | Phase 4+ | ✅ Released |
| `v1.3.0` | Sprint 8 — Multi-Tenant Auth | Phase 4+ | ✅ Released |
| `v1.4.0` | Sprint 9 — PostgreSQL Migration | Phase 4+ | ✅ Released |
| `v1.5.0` | Sprint 10 — Streaming Responses | Phase 4+ | ✅ Released |
| `v1.6.0` | Sprint 11 — Burnout Trend Chart | Phase 4+ | ✅ Released |
| `v1.7.0` | Sprint 12 — Weekly Digest | Phase 4+ | ✅ Released |
| `v1.8.0` | Sprint 13 — Demo Polish + Shareable Deploy | Phase 4+ | ✅ Released |
| `v1.9.0` | Sprint 14 — Structured Logging + SEO/LLM Discoverability | Phase 4+ | ✅ Released |
