# Kinetic — CLAUDE.md

**Author:** Karl Johnson <hirekarl@proton.me>
**Project:** Bio-Operational Triage Engine — Pursuit AI-Native L1 Capstone
**Timeline:** 10-day sprint to demo-ready prototype
**Stack:** Python 3.12 / uv / FastAPI / Pydantic v2 / Gemini 2.5 Flash + Instructor · React 18 / TypeScript / Vite / Vitest / Playwright

---

## Project Overview

Kinetic is a personal infrastructure management system for high-performance engineers. It monitors three domains — biometrics (sleep/nutrition/burnout), domestic logistics (task triage + outsourcing ROI), and relationships (connection margin + interaction sprints) — and surfaces a unified, prioritized triage list so the user can stay sustainable at high velocity.

**Architecture in one sentence:** A natural-language check-in message → Gemini parses it into typed Pydantic models → a lead orchestrator routes to specialist agents → agents return typed status objects → the frontend renders a live split-panel dashboard.

---

## Architecture

```
User (chat input)
    │ free-text message
    ▼
LLM Parser (Gemini 2.5 Flash + Instructor)
    │ CheckInPayload (typed Pydantic)
    ▼
Lead Orchestrator (src/kinetic/orchestrator/lead.py)
    ├─ if payload.bio       → BioArchivist       → BioStatus
    ├─ if payload.logistics → LogisticsFixer      → LogisticsStatus
    └─ if payload.relational→ RelationalDiplomat  → RelationalStatus
    │
    ▼ aggregate
SystemHealthPayload (overall_status + triage_items + roi_summary)
    │ JSON via POST /api/checkin
    ▼
React Dashboard (frontend/src/)
    ├─ Left panel:  ChatPanel component (message input)
    └─ Right panel: Dashboard component (status cards + triage list)
```

---

## Module Map

```
src/kinetic/
  __init__.py              package version (__version__)
  main.py                  FastAPI app, CORS config, router mount
  models/
    inputs.py              CheckInPayload + sub-models (canonical input contracts)
    outputs.py             SystemHealthPayload + sub-models (canonical output contracts)
  agents/
    base.py                Agent Protocol + AgentResult base class
    bio_archivist.py       sleep/nutrition tracking + burnout forecast
    logistics_fixer.py     task triage + outsourcing ROI
    relational_diplomat.py connection margin + interaction sprints
  orchestrator/
    lead.py                routing logic + status aggregation
  parsing/
    llm_parser.py          Gemini 2.5 Flash + Instructor integration
  api/
    routes.py              FastAPI APIRouter (POST /api/checkin)

tests/
  conftest.py              shared fixtures (sample payloads, health objects)
  unit/test_models.py      model validation tests
  unit/                    agent logic, orchestrator, parser tests (Phase 2+)
  integration/             end-to-end API tests (Phase 3+)

frontend/src/
  types/index.ts           TypeScript interfaces mirroring Python output models
  App.tsx                  split-panel root component
  components/ChatPanel/    natural-language input + streaming display
  components/Dashboard/    status cards, triage list, ROI summary
  hooks/                   useCheckin, useSystemHealth, etc.
  test/setup.ts            Vitest + @testing-library/jest-dom bootstrap
  e2e/                     Playwright + axe-core accessibility specs
```

---

## Roadmap

`ROADMAP.md` at the repo root tracks sprint-by-sprint progress against the PRD's four phases. Each sprint targets a version bump. The `/docs-keeper` agent owns this file — check it off as tasks complete and flip sprint status emoji (⬜ → 🔄 → ✅) at the end of each cycle.

| Sprint | Version | Focus | Status |
|--------|---------|-------|--------|
| Sprint 0 | `v0.1.0` | Bootstrap | ✅ |
| Sprint 1 | `v0.2.0` | Agent Logic | ⬜ |
| Sprint 2 | `v0.3.0` | LLM Parsing | ⬜ |
| Sprint 3 | `v0.4.0` | Frontend Core | ⬜ |
| Sprint 4 | `v0.5.0` | Integration + ROI | ⬜ |
| Sprint 5 | `v1.0.0` | Polish + Demo | ⬜ |

---

## Dev Commands

All Python commands use `uv run` — no manual venv activation needed.

```bash
# ── Environment setup ──────────────────────────────────────────────────────
uv sync                          # install all deps (runtime + dev group)
cp .env.example .env             # set GEMINI_API_KEY

# ── Backend ───────────────────────────────────────────────────────────────
uv run uvicorn kinetic.main:app --reload --port 8000
uv run pytest                    # all tests with coverage
uv run pytest -m unit            # unit tests only
uv run pytest -m integration     # integration tests only
uv run ruff check src/ tests/    # lint
uv run ruff format src/ tests/   # format
uv run mypy src/kinetic --strict # type check

# ── Frontend ──────────────────────────────────────────────────────────────
cd frontend
npm install
npm run dev                      # Vite dev server on :5173 (proxies /api → :8000)
npm run test                     # Vitest unit tests
npm run test:coverage            # Vitest + coverage report
npm run lint                     # ESLint (includes jsx-a11y)
npm run format                   # Prettier
npm run typecheck                # tsc --noEmit
npm run e2e                      # Playwright e2e + axe audits (needs dev server)
npm run build                    # production build

# ── Pre-commit ────────────────────────────────────────────────────────────
pre-commit install               # install hooks (run once after cloning)
pre-commit run --all-files       # run all hooks manually

# ── Dependency management (uv) ────────────────────────────────────────────
uv add <package>                 # add runtime dependency
uv add --group dev <package>     # add dev-only dependency
uv remove <package>              # remove dependency
uv lock                          # regenerate uv.lock
uv sync --upgrade                # upgrade all deps within constraints
```

---

## Environment Variables

Create `.env` at the project root (never commit it):

```
GEMINI_API_KEY=your_key_here
```

The app reads this via `python-dotenv`. The `.gitignore` already excludes `.env`.

---

## SemVer & Release Ceremony

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Every commit must use one of:

```
feat:     new feature → bumps MINOR
fix:      bug fix     → bumps PATCH
docs:     docs only   → bumps PATCH
style:    formatting  → bumps PATCH
refactor: refactor    → bumps PATCH
test:     tests       → bumps PATCH
chore:    maintenance → bumps PATCH
perf:     performance → bumps PATCH
ci:       CI changes  → bumps PATCH
build:    build system→ bumps PATCH
revert:   revert      → bumps PATCH

BREAKING CHANGE: (footer) → bumps MAJOR
```

**To cut a release:**
```bash
./scripts/release.sh
```

The ceremony script:
1. Validates all commits since the last tag follow the spec
2. Shows a dry-run preview of the version bump and new CHANGELOG entries
3. Prompts for confirmation
4. Runs `cz bump --changelog` (bumps version in `pyproject.toml` + `__init__.py`, updates `CHANGELOG.md`, creates release commit + tag)
5. Prompts to push commit and tag

---

## TDD Workflow

Every feature follows **Red → Green → Refactor** strictly:

1. **Red:** Write failing test(s) that express the acceptance criteria
2. **Green:** Write the minimum implementation to pass the tests
3. **Refactor:** Clean up while keeping tests green

**Quality gates (enforced by CI and pre-commit):**
- `pytest` coverage ≥ 80% (`--cov-fail-under=80`)
- `mypy --strict` passes with zero errors
- `ruff check` passes with zero warnings
- `npm run test:coverage` coverage ≥ 80% on all thresholds
- `npm run lint` passes with zero errors
- Playwright e2e + axe audits pass (zero WCAG 2.1 AA violations)

---

## Multi-Agent Dev Team

Six specialist agents are available as Claude Code slash commands:

| Command | Agent | Responsibility |
|---------|-------|---------------|
| `/architect` | Architect | Decompose features → design docs + task cards with typed contracts and acceptance criteria |
| `/backend-dev` | Backend TDD Dev | Write failing Python tests first, then implementation; enforce mypy + 80% coverage |
| `/frontend-dev` | Frontend TDD Dev | Write failing Vitest/Playwright tests first, then React/TS implementation |
| `/qa-reviewer` | QA Reviewer | Validate test quality, coverage gaps, integration scenarios; approve or block |
| `/security-reviewer` | Security Reviewer | Run bandit/pip-audit/npm audit; check secrets, input validation, OWASP Top 10 |
| `/docs-keeper` | Docs Keeper | Keep CLAUDE.md, GEMINI.md, inline docs, and memory in sync with code reality |

---

## Handoff Protocol

Work flows: **Architect → Backend/Frontend Dev → QA Reviewer → Security Reviewer → Docs Keeper**

Every handoff includes a **task card** with:

```markdown
## Task: [Feature Name]

**Design ref:** [path to design doc or inline spec]
**API contract:** [typed function signature or HTTP endpoint schema]
**Acceptance criteria:**
- [ ] ...

**TDD checklist:**
- [ ] Failing test written
- [ ] Implementation passes tests
- [ ] mypy strict passes / tsc --noEmit passes
- [ ] Coverage ≥ 80%
- [ ] Linting passes

**Dependencies:** [other tasks that must complete first]
**Blockers:** [known unknowns]
```

Code cannot advance to the next stage without all checklist items complete.

---

## Pydantic Contracts (Canonical Truth)

The Python models in `src/kinetic/models/` are the single source of truth for data shapes. The TypeScript interfaces in `frontend/src/types/index.ts` mirror them exactly. When changing a Python model, update the TS types in the same PR.

**Input contract:**
- `CheckInPayload` — parsed from user's natural-language message; all sub-models Optional
- Sub-models: `BioInput`, `LogisticsInput`, `RelationalInput`

**Output contract:**
- `SystemHealthPayload` — returned by orchestrator, consumed by frontend; one consistent shape regardless of which agents fired
- Sub-models: `BioStatus`, `LogisticsStatus`, `RelationalStatus`, `TriageItem`, `ROISummary`

---

## Accessibility Standards

All UI must pass WCAG 2.1 AA. The `eslint-plugin-jsx-a11y` strict config and `@axe-core/playwright` e2e audits enforce this automatically.
