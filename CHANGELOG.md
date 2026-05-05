# Changelog

All notable changes to Kinetic are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

### Test

- Restore 100% backend coverage: add 5 `complete_subtask` unit tests to `test_postgres_client_unit.py` covering happy path, KeyError, ValueError, auto-completion, and idempotency; add `# pragma: no cover` to `DatabaseClient` Protocol class (stubs are type-only, not executable)

## v1.10.0 (2026-05-04)

### Feat

- **logistics**: non-destructive upsert, field-level merge, subtask check-off

### Fix

- **readme**: replace static version badge with dynamic GitHub tag badge

## v1.9.2 (2026-05-04)

### Fix

- **frontend**: remove hardcoded fake system status from landing page
- audit and correct all Gemini API usage for idiomaticity
- **liaison**: convert 'assistant' role to 'model' before Gemini API calls
- read FastAPI version from __version__ instead of hardcoded 0.1.0
- **frontend**: resolve all ESLint errors introduced by line-ending renormalize
- **frontend**: restore noUncheckedIndexedAccess guard + sync version to landing page

## v1.9.1 (2026-05-04)

### Fix

- **streaming**: clear loading state when SSE stream closes without done event

## v1.9.0 (2026-05-03)

### Feat

- **sprint14**: add structured logging and SEO/LLM discoverability
- Render deploy hardening + deployment checklist
- **seo**: add comprehensive metadata, PWA manifest, and brand assets to public/
- **brand**: add brand asset generator + 6 high-res PNG exports
- **frontend**: add marketing landing page, SVG logo, and react-router routing
- **demo**: Sprint 13D demo artifact suite + frontend polish
- **docs**: add robust cross-platform presentation script using rich
- **docs**: switch to present TUI for cross-platform demo support
- **docs**: add prezo TUI presentation deck for demo polish

### Fix

- **deploy**: remove invalid plan field from static site service
- **deploy**: correct render.yaml Blueprint schema errors
- **stream**: filter paused contacts before agents SSE event
- **a11y**: increase "Return to base" link contrast to pass WCAG 2 AA
- **docs**: resolve present TUI crash by pinning mistune to 2.x
- **release**: use $current_version template syntax in bump_message for commitizen v4

### Refactor

- modularize lead.py, operational_liaison.py, and App.tsx

## v1.8.0 (2026-04-28)

### Feat

- **ui**: Simulate Week button + mobile-responsive layout (Sprint 13 A+B)
- **demo**: POST /api/demo/simulate — 5 scripted check-ins with historical timestamps

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
