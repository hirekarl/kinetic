# Changelog

All notable changes to Kinetic are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

### Added
- Mobile-responsive layout: app now stacks vertically on small screens (chat panel above dashboard) and expands to side-by-side on large screens
- "Simulate Week" button (demo tenant only): inserts 5 pre-scripted check-ins spanning 7 historical days, then auto-refreshes digest and burnout chart to show a populated dashboard state
- `POST /api/demo/simulate` backend route: 403-gated to demo tenant; `simulate_week()` service with configurable scripted trajectories (baseline → decline → peak stress → recovery)
- `insert_checkin_at()` added to `DatabaseClient` Protocol (both SQLite and PostgreSQL backends) to support historical timestamp injection
- README.md updated: numbered setup steps, inline bcrypt hash generation command, "Running the demo" section with Simulate Week instructions, sprint table extended through Sprint 13
- `docs/DEMO.md` updated: 5-section verbal opening (Problem → Root Cause → Solution → Architecture → Preview), Pre-Demo checklist updated to use Simulate Week button, streaming Q&A corrected (streaming ships in Sprint 10 via SSE), "What's Next" close added, Render URL slot added
- `docs/PRESENTATION.md` added: named persona (Karl, senior SWE at growth-stage startup), measurable success metric, technology choices rationale (Gemini + Instructor, dual-mode DB Protocol, SSE streaming)

## v1.7.0 (2026-04-28)

### Feat

- **ui**: WeeklyDigestCard — collapsible digest with refresh, timestamp, error states (Sprint 12)
- **digest**: weekly digest backend — GET /api/digest + generate_digest service (Sprint 12)

### Fix

- **db**: guard get_burnout_series against days<=0 to prevent datetime precision race on CI

## v1.6.0 (2026-04-28)

### Feat

- **ui**: burnout trend chart — BioStatusCard 14-day sparkline + DB series (Sprint 11)

## v1.5.0 (2026-04-28)

### Feat

- **streaming**: Sprint 10 — SSE streaming backend + frontend client (v1.5.0)

## v1.4.0 (2026-04-27)

### Feat

- **db**: PostgreSQL migration — dual-mode DatabaseClient with asyncpg (Sprint 9)

## v1.3.0 (2026-04-26)

### Feat

- **auth**: multi-tenant auth — backend + frontend (Sprint 8)

## v1.2.0 (2026-04-26)

### Feat

- **ui**: agent dispatch log panel — Sprint 7

## v1.1.0 (2026-04-26)

### Feat

- **scenarios**: adversarial scenario test suite + live runner — Task B2
- **liaison**: prompt hardening with 5 situational-awareness rules — Task B1
- **ui**: triage task completion UI with optimistic removal — Task A2
- **task-completion**: server-persisted task completion — Task A1
- **liaison**: conversational history, specialist routing, and contact pause lifecycle
- **frontend**: 7-day sleep sparkline on Bio card

## v1.0.0 (2026-04-26)

### Feat

- **demo**: add demo script, seed script, and verify end-to-end flow
- **frontend**: Sprint 6 accessibility final audit — contrast + screen reader fixes
- **frontend**: Sprint 6 onboarding flow with localStorage persistence
- **frontend**: soften error copy and add Retry CTA to error banner
- **main**: add lifespan startup warning when GEMINI_API_KEY is absent
- **frontend**: BehavioralProfilePanel — collapsible behavioral profile section
- **frontend**: Sprint 4 e2e tests, a11y contrast fixes, and component unit tests
- **orchestrator**: wire behavioral memory into orchestrator and liaison
- **services**: implement Pattern Detector background service
- **persistence**: implement Behavioral Memory data layer
- **persistence**: implement state hydration on page refresh
- **logistics**: implement granular checklists for task tracking
- **debug**: add reset button to wipe database during testing
- **liaison**: implement Operational Liaison for executive function support
- **persistence**: implement LadybugDB graph persistence for historical accountability
- **integration**: polish frontend integration with loading and error states
- **roi**: implement ROI calculator and performance yield summary
- **frontend**: implement Sprint 2 & 3 — LLM parsing + React dashboard

### Fix

- **e2e**: mock history endpoint in Firefox-flaky interaction tests
- **db**: remove dead embedding code from SqliteClient
- **tests**: mock orchestrate in checkin unit test to avoid GEMINI_API_KEY dependency
- **db,services**: clear behavioral_profiles on reset; harden JSON parser
- **persistence**: resolve LadybugDB binder errors with explicit casting
- **orchestrator**: implement cumulative context merging
- **liaison**: use correct gemini-2.5-flash model as per PRD
- **integration**: resolve connectivity issues on Windows
- **backend**: add missing jsonref dependency
- **frontend**: use explicit IPv4 for proxy target
- **parsing**: update instructor mode for google-genai SDK
- **backend**: load environment variables at startup

### Refactor

- **persistence**: pivot from LadybugDB to SQLite for stability
- **persistence**: comprehensive database audit and parallel-safety fix
- **persistence**: switch to Gemini embeddings for reliability
- **parsing**: upgrade to modern google-genai SDK

## v0.2.0 (2026-04-25)

### Feat

- **agents**: implement Sprint 1 — all three agents + orchestrator

### Fix

- scope Vitest coverage to runtime source files only

## v0.1.0 (2026-04-25)

### Feat

- bootstrap project infrastructure (v0.1.0)
