# Changelog

All notable changes to Kinetic are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

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
