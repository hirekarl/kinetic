# Changelog

All notable changes to Kinetic are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)


### Added
- Project bootstrap: `pyproject.toml` with uv, ruff, mypy strict, pytest, commitizen
- Pydantic v2 input models: `CheckInPayload`, `BioInput`, `LogisticsInput`, `RelationalInput`
- Pydantic v2 output models: `SystemHealthPayload`, `BioStatus`, `LogisticsStatus`, `RelationalStatus`, `TriageItem`, `ROISummary`
- Agent Protocol base class and typed stubs: `BioArchivist`, `LogisticsFixer`, `RelationalDiplomat`
- Lead orchestrator skeleton with routing logic
- LLM parser stub (Gemini 2.5 Flash + Instructor integration point)
- FastAPI app skeleton with `POST /api/checkin` and `GET /health`
- React + TypeScript frontend scaffold: Vite, Vitest, ESLint flat config, Prettier
- Playwright e2e testing with `@axe-core/playwright` accessibility audits
- `eslint-plugin-jsx-a11y` strict rules in ESLint config
- Pre-commit hooks: ruff, mypy, prettier, conventional-pre-commit, hygiene checks
- SemVer release ceremony script (`scripts/release.sh`)
- `CLAUDE.md` and `GEMINI.md` with OS auto-detection startup ritual
- Multi-agent dev team slash commands: `/architect`, `/backend-dev`, `/frontend-dev`, `/qa-reviewer`, `/security-reviewer`, `/docs-keeper`
- Bootstrap unit tests (8 passing, >80% coverage on models)
- `ROADMAP.md` — 6-sprint development roadmap with checkbox tracking tied to PRD phases and SemVer version targets

[Unreleased]: https://github.com/hirekarl/kinetic/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/hirekarl/kinetic/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/hirekarl/kinetic/releases/tag/v0.1.0

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
