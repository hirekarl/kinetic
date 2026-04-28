# Changelog

All notable changes to Kinetic are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

### Added
- `render.yaml` — Render Blueprint for one-command deployment (FastAPI API service + React static site + PostgreSQL basic-256mb database)
- `.python-version` — pins Python 3.12 for uv and Render build environment
- `DatabaseClient` Protocol (`src/kinetic/db/base.py`) — shared `@runtime_checkable` interface satisfied by both SQLite and PostgreSQL backends
- `PostgresClient` (`src/kinetic/db/postgres_client.py`) — asyncpg-backed implementation with per-tenant row isolation (`tenant TEXT NOT NULL` column on all 7 tables) and idempotent `_migrate()` DDL
- Dual-mode `get_db()` in `orchestrator/lead.py` — returns `PostgresClient` when `DATABASE_URL` is set (Render production), `SqliteClient` otherwise (local dev unchanged)
- `asyncpg>=0.31.0` runtime dependency

### Changed
- `src/kinetic/main.py` lifespan now creates and closes an asyncpg connection pool when `DATABASE_URL` is set; logs info when falling back to SQLite
- `src/kinetic/main.py` CORS origins now include `FRONTEND_URL` env var at startup (required for Render production deployment)

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
