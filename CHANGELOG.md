# Changelog

All notable changes to Kinetic are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

### Added
- `src/kinetic/logging_config.py` — `is_production()` + idempotent `setup_logging()`; structlog processor chain with `stdlib.LoggerFactory` bridge; dev: colorized `ConsoleRenderer`, prod (`RENDER=true` or `LOG_FORMAT=json`): `JSONRenderer`; `cache_logger_on_first_use=False` for pytest `capture_logs()` compatibility
- `src/kinetic/middleware/logging.py` — `StructlogRequestMiddleware`: binds `request_id`, `path`, `method`, and (after auth) `tenant` to structlog context vars per request; emits `request.start`, `request.done` (with `status_code` + `duration_ms`), and `request.error` log events
- Structured log events across all callsites: `auth.login.success/failure`, `auth.token.expired/invalid`, `agents.dispatch`, `agent.error`, `llm.parse/call/stream/metadata.start/done`, `digest.cache.hit`, `digest.generate.start/done/error`, `pattern.detect.start/done/skipped`, `checkin.start/done`, `task.completed`, `db.pool.created/closed`, `db.sqlite.fallback`
- `structlog>=24.0` runtime dependency (installed as 25.5.0)
- `tests/unit/test_logging_config.py` — 9 tests; `tests/unit/test_logging_middleware.py` — 8 tests

### Added
- `src/kinetic/orchestrator/triage.py` — pure aggregation/filter helpers extracted from `lead.py`: `calculate_roi`, `aggregate_status`, `assign_stable_ids`, `filter_paused_contacts`, `filter_paused_relational_status`
- `src/kinetic/agents/liaison_context.py` — context formatter functions extracted from `operational_liaison.py`: `format_bio_status`, `format_logistics_status`, `format_relational_status`, `format_behavioral_summary`, `format_profiles`
- `frontend/src/hooks/useChat.ts` — custom hook owning all chat/streaming state and handlers; extracted from `App.tsx`
- `frontend/src/hooks/useDigest.ts` — custom hook owning digest state and refresh logic; extracted from `App.tsx`

### Changed
- `src/kinetic/orchestrator/lead.py` — added `_AgentRunResult` dataclass and `_run_agents()` async helper to deduplicate the agent-execution block shared between `orchestrate()` and `orchestrate_stream()`; added `_fire_pattern_detection()` helper; imports triage helpers from `triage.py`
- `src/kinetic/agents/operational_liaison.py` — formatter functions moved to `liaison_context.py`; all models and the `OperationalLiaison` class unchanged
- `frontend/src/App.tsx` — reduced from ~410 to ~220 lines; chat and digest state fully delegated to `useChat` and `useDigest` hooks

### Added
- `scripts/migrate.py` — standalone asyncpg pre-deploy DDL migration script; run as `preDeployCommand` on Render before the app starts; imports `_DDL` from `postgres_client` as single source of truth; idempotent, safe to re-run
- `docs/DEPLOY.md` — end-to-end Render deployment checklist: credentials.toml prep, Blueprint deploy, Secret File upload, per-service env var tables, post-deploy verification, tenant lifecycle, SECRET_KEY rotation

### Changed
- `render.yaml` — `kinetic-api` upgraded to `plan: starter` (always-on, eliminates cold-start spin-down for demos); added `healthCheckPath: /health` so Render gates traffic on a live 200 response; added `preDeployCommand: uv run python scripts/migrate.py` to run DDL migrations before startup
- Marketing landing page at `/` with hero, agent domain cards, and how-it-works sections
- `KineticLogo` SVG mark (three-line K convergence) used in landing page and as favicon
- URL-based routing via react-router-dom (`/` landing, `/login` auth, `/app` dashboard)
- Brand asset generator (`npm run brand`) producing og-card, twitter-card, icon-512, icon-192, wordmark PNGs
- Comprehensive SEO metadata: Open Graph, Twitter Card, JSON-LD structured data, PWA manifest
- `← Return to base` back-link on login screen
- `frontend/e2e/live-demo.spec.ts` — Playwright demo recording script: 12-section mocked flow covering all rubric requirements; smooth scroll, mouse cursor overlay, simulated Gemini latency delays, 1920×1080 headless video capture
- `frontend/playwright-demo.config.ts` — dedicated Playwright config for demo recording (headless, 300s timeout, video: on, 1920×1080)
- `docs/NARRATION.md` — video voiceover script (~4 min) for the Playwright video artifact; three-part structure with [HOLD] markers aligned to screen recording beats

### Changed
- `docs/DEMO.md` — complete rewrite as live in-person presentation script; rubric-ordered (Problem → Root Cause → Solution → Live Demo → What's Next) with exact spoken lines, typed inputs, pre-demo setup checklist, and troubleshooting table

### Fixed
- `WeeklyDigestCard.tsx` — removed erroneous `if (!digest && !isLoading) return null` guard that broke the intentional no-data empty state
- `BehavioralProfilePanel.tsx` — removed useless `= []` default on required non-optional prop
- `ROISummaryCard.tsx` — removed unreachable `if (!data) return null` guard on non-nullable prop
- `RelationalStatusCard.tsx` — removed unnecessary `?? []` fallbacks on `string[]` fields that TypeScript already guarantees non-null

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
