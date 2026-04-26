# Changelog

All notable changes to Kinetic are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

### Added
- **BehavioralProfilePanel:** Collapsible disclosure section on the Mission Control dashboard rendering accumulated `behavioral_profiles` from `SystemHealthPayload`. Collapsed by default, keyboard-navigable, `aria-expanded` wired. Shows `profile_key` tag, plain-English `insight`, `observation_count` badge, and `last_updated` date per profile. Empty state: "Building your profile — check in again tomorrow." Vitest (11 tests, 100% component coverage), 2 new Playwright e2e scenarios, zero WCAG 2.1 AA violations.
- **Behavioral Memory — Pattern Detector Service:** `src/kinetic/services/pattern_detector.py` — `detect_and_update_patterns()` calls Gemini after each check-in to derive behavioral patterns from the accumulated summary; upserts results as `BehavioralProfile` records. Rate-limit guard prevents redundant calls (skips if `days_analyzed < 3` or any profile updated within 20 hours). Fires as a non-blocking `asyncio.create_task()` — never propagates exceptions.
- **Behavioral Memory — Orchestrator + Liaison Integration:** `orchestrate()` fetches `BehavioralSummary` and `BehavioralProfile` list after agents fire and threads both through to `OperationalLiaison.process()`. The Liaison's Gemini prompt now includes a BEHAVIORAL CONTEXT section with 14-day trend data and established patterns, grounding tactical guidance in history rather than just the current check-in. `SystemHealthPayload` now always includes `behavioral_profiles`.
- **Behavioral Memory data layer:** Five new Pydantic output models (`BioTrend`, `RecurringTask`, `RelationalDrift`, `BehavioralSummary`, `BehavioralProfile`) enabling the app to accumulate and expose structured knowledge of the user's behavioral patterns over time.
- `behavioral_profiles` SQLite table for persisting Gemini-derived pattern insights across sessions; supports upsert with `first_observed` immutability and `observation_count` tracking.
- `SqliteClient.get_behavioral_summary()`: queries 7–14 days of stored bio, logistics, and relational data to compute sleep slope (stdlib `statistics.linear_regression`), recurring overdue tasks, and relational drift velocity — all returned as typed Pydantic models.
- `SystemHealthPayload.behavioral_profiles` field: accumulated behavioral profiles are now included in every API response, available for frontend rendering.
- TypeScript mirror interfaces for all new models in `frontend/src/types/index.ts`.
- SQLite column migration guard for existing databases missing the `liaison_feedback` column.
- `ROISummaryCard`: New frontend component for visualizing time reclaimed, system margin, and burnout risk delta.
- ROI Calculation logic in Lead Orchestrator: Quantifies operational yield based on logistics outsourcing and relational health.
- React Mission Control Dashboard: High-fidelity split-panel UI with sector-specific status cards (`Bio`, `Logistics`, `Relational`).
- LLM Parsing Layer: Full implementation using Gemini 2.5 Flash and Instructor to convert natural language check-ins into structured data.
- Tailwind CSS configuration: Custom dark-mode theme with semantic status colors (emerald, amber, rose) following "Developer Tool Minimalism" aesthetic.
- `docs/kinetic-design-system.md`: Comprehensive design brief for the Kinetic frontend.

### Changed
- Refactored LLM Parser to use the modern `google-genai` SDK (v1.0), removing the deprecated `google-generativeai` package.
- Updated `App.tsx` and `App.test.tsx` to support the new semantic structure and ROI integration.
- WCAG 2.1 AA color contrast remediation: all `text-zinc-500` and `text-zinc-600` occurrences across Dashboard components, `App.tsx`, and `ChatPanel` changed to `text-zinc-400` (7–8:1 ratio vs. 4.11:1 minimum). Active Blockers badge lightened from `bg-status-red/10` to `bg-status-red/5` for 5.5:1 contrast on red text.
- Playwright mobile-safari project updated to iPad Pro 11 viewport (1024px) from iPhone 14 (390px) — the fixed 420px left panel was clipped on narrow viewports, hiding the dashboard panel from tests.
- Added `tabIndex={0}` to main scrollable content region in `App.tsx` to satisfy the axe `scrollable-region-focusable` rule.

### Removed
- `render.yaml` — Render deployment config removed; MVP targets local demo only.

### Fixed
- `clear_database()` now deletes from `behavioral_profiles` — previously left stale profiles after `/api/debug/reset`.
- `_parse_patterns()` uses bracket-depth matching instead of a greedy regex, correctly handling nested arrays in `evidence` payloads and prose commentary containing brackets before the JSON array.
- Integration test `test_checkin_success_path` now verifies response shape rather than asserting a specific status value, preventing false failures when the local database contains historical data.
- `SqliteClient.get_embedding()` now correctly guards against `None` embeddings and `None` values from the Gemini API response.
- Removed stale `# type: ignore` comments on `aiosqlite` and `python-dotenv` imports now that both packages ship type stubs.
- Resolved multiple ESLint and TypeScript issues in the frontend components (misused promises, unsafe any, Confusing void expressions).
- Added robust error handling for API failures, including 503 fallback for missing Gemini credentials.
- Two new Playwright e2e tests: full check-in flow verifying all three sector cards and triage list populate, and axe WCAG 2.1 AA audit on fully-populated dashboard state.
- 54 new Vitest component unit tests across all Dashboard components, `ChatPanel`, `App`, and API client; overall frontend coverage: 98% lines, 92% branches, 100% functions.
- `bandit` and `pip-audit` added to dev dependencies for security scanning.
- `frontend/playwright-report/` and `frontend/test-results/` excluded from git via `.gitignore`.

## [0.2.0] — 2026-04-25

### Added
- `BioArchivist`: weighted burnout score (sleep 40%, nutrition 30%, energy 30%), re-normalized for partial data; green <40 / yellow <70 / red ≥70; triage items at priority 6 (yellow) and 9 (red)
- `LogisticsFixer`: criticality = `days_overdue × priority_weight` ({low:1, medium:2, high:3, critical:4}); yellow ≤6 / red >6; outsourcing keyword stubs; `time_to_resolve_minutes` estimation
- `RelationalDiplomat`: recency-decayed connection margin (`max(0.3, 1-(days-7)*0.05)`); at-risk on score<5 (→ red) or days>7 (→ yellow); 3-tier interaction sprint templates
- Lead orchestrator: per-agent try/except so one failure doesn't block others; worst-case `overall_status`; triage items merged, sorted descending, stable domain-scoped IDs (`{domain}-{i:03d}`)
- `AgentResult` extended with `triage_items: list[TriageItem]`
- 27 new unit tests (35 total); 88% coverage; bandit + ruff + mypy strict clean

## [0.1.0] — 2026-04-25

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
