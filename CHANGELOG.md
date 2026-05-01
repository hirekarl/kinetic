# Changelog

All notable changes to Kinetic are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

### Added
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
