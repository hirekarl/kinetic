# Changelog

All notable changes to Kinetic are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

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

[Unreleased]: https://github.com/karl-johnson/kinetic/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/karl-johnson/kinetic/releases/tag/v0.1.0
