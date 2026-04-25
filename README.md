# Kinetic

**Bio-Operational Triage Engine** — personal infrastructure management for high-performance engineers.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-managed-blueviolet?logo=astral&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://docs.astral.sh/ruff/)
[![mypy: strict](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/)
[![TypeScript: strict](https://img.shields.io/badge/typescript-strict-blue?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Sprint](https://img.shields.io/badge/sprint-1%20of%205-orange)](ROADMAP.md)

---

## What It Is

High-performing engineers routinely fall into the **High-Performance Trap**: relentless output accumulates hidden personal debt — sleep, logistics, relationships — until a crash forces a reset.

Kinetic is a mission-control dashboard that surfaces that debt before it compounds. You brief it in natural language once a day. It routes your input through three specialist agents and hands back a prioritized, data-driven triage list so you can clear high-leverage actions in minutes and return to flow.

```
"Slept 5 hours, ate okay, feeling disconnected from Marcus."
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│  Kinetic                              ● YELLOW           │
├──────────────────────┬──────────────────────────────────┤
│  > Slept 5 hours,    │  BIO          ● yellow           │
│    ate okay,         │  Burnout: 62  Sleep debt: 3.5h   │
│    feeling           │  Hard stop at 11pm recommended   │
│    disconnected      ├──────────────────────────────────┤
│    from Marcus.      │  LOGISTICS    ● yellow           │
│                      │  Laundry overdue: 2d             │
│  Brief your system.  │  → Pickup tonight (~$25, 2h ROI) │
│  What's your status? ├──────────────────────────────────┤
│                      │  RELATIONAL   ● red              │
│  ________________    │  Marcus: 11d, score 4/10         │
│  [Send]              │  → Text to schedule a call (30s) │
└──────────────────────┴──────────────────────────────────┘
```

---

## How It Works

A single natural-language check-in message is parsed by **Gemini 2.5 Flash + Instructor** into a typed `CheckInPayload`. The **Lead Orchestrator** routes the payload to whichever specialist agents are relevant:

| Agent | Domain | Output |
|-------|--------|--------|
| **Bio-Metric Archivist** | Sleep · Nutrition · Energy | Burnout score + forecast |
| **Logistics Fixer** | Domestic tasks + outsourcing ROI | Criticality flags + vendor suggestions |
| **Relational Diplomat** | Connection margin + vibe checks | Interaction sprint recommendations |

The orchestrator aggregates agent outputs into a single `SystemHealthPayload` — one consistent shape the React frontend consumes, regardless of which agents fired.

---

## Stack

**Backend**
- Python 3.12, [uv](https://docs.astral.sh/uv/) for environment + dependency management
- [FastAPI](https://fastapi.tiangolo.com/) · [Pydantic v2](https://docs.pydantic.dev/) · [Instructor](https://python.useinstructor.com/) + [Gemini 2.5 Flash](https://ai.google.dev/)
- mypy strict · ruff · pytest + pytest-cov

**Frontend**
- React 18 · TypeScript strict · [Vite](https://vitejs.dev/)
- [Vitest](https://vitest.dev/) · [Playwright](https://playwright.dev/) · [@axe-core/playwright](https://github.com/dequelabs/axe-core-npm)
- ESLint flat config (TypeScript-ESLint + jsx-a11y strict) · Prettier

**Tooling**
- [Commitizen](https://commitizen-tools.github.io/commitizen/) SemVer (Conventional Commits)
- pre-commit hooks: ruff, mypy, prettier, conventional-pre-commit
- [Render Blueprint](https://render.com/docs/blueprint-spec) deployment (`render.yaml`)

---

## Getting Started

### Prerequisites
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js ≥ 18 + npm
- A [Gemini API key](https://aistudio.google.com/app/apikey)

### Local dev

```bash
# Clone and set up
git clone https://github.com/hirekarl/kinetic.git
cd kinetic

# Backend
cp .env.example .env          # add your GEMINI_API_KEY
uv sync                       # installs Python deps + creates .venv
pre-commit install            # wire up commit hooks (run once)
uv run uvicorn kinetic.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                   # Vite dev server on :5173, proxies /api → :8000
```

Open `http://localhost:5173`.

### Running tests

```bash
# Python
uv run pytest                 # unit tests + coverage report
uv run pytest -m integration  # integration tests (requires GEMINI_API_KEY)

# Frontend
cd frontend
npm run test:coverage         # Vitest unit tests
npm run e2e                   # Playwright + axe accessibility audit (needs dev server)
```

---

## Project Status

See [ROADMAP.md](ROADMAP.md) for the full sprint-by-sprint breakdown.

| Sprint | Focus | Version | Status |
|--------|-------|---------|--------|
| Sprint 0 | Bootstrap — tooling, typed skeletons, agent team | `v0.1.0` | ✅ Released |
| Sprint 1 | Agent logic — all three agents + orchestrator | `v0.2.0` | 🔄 In progress |
| Sprint 2 | LLM parsing layer — Gemini + Instructor end-to-end | `v0.3.0` | ⬜ |
| Sprint 3 | Frontend core — ChatPanel + Dashboard components | `v0.4.0` | ⬜ |
| Sprint 4 | Integration + ROI calculator | `v0.5.0` | ⬜ |
| Sprint 5 | Polish, accessibility audit, demo prep | `v1.0.0` | ⬜ |

**Demo deadline:** 2026-05-03 · **MVP deadline:** 2026-05-05

---

## Development Workflow

This project uses a **multi-agent TDD team** via Claude Code slash commands. Work flows through six specialist agents:

```
/architect       → design doc + typed task card
     ↓
/backend-dev     → failing tests first, then implementation (Python)
/frontend-dev    → failing tests first, then implementation (React/TS)
     ↓
/qa-reviewer     → coverage validation + integration scenarios
     ↓
/security-reviewer → secrets scan, input validation, dependency audit
     ↓
/docs-keeper     → CLAUDE.md · GEMINI.md · ROADMAP.md · CHANGELOG.md in sync
```

Every commit follows [Conventional Commits](https://www.conventionalcommits.org/). Releases are cut with `./scripts/release.sh`.

---

## Deployment

The project ships a `render.yaml` [Blueprint](https://render.com/docs/blueprint-spec). Connect the repo in the Render dashboard and two services are provisioned automatically:

- **kinetic-api** — Python/FastAPI web service
- **kinetic-frontend** — React/Vite static site

Set `GEMINI_API_KEY` on the API service and `VITE_API_BASE_URL=https://kinetic-api.onrender.com` on the frontend service, then deploy.

---

## Author

**Karl Johnson** · [hirekarl@proton.me](mailto:hirekarl@proton.me)

Built for the [Pursuit](https://www.pursuit.org/) AI-Native L1 Capstone.
