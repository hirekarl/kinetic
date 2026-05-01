# Kinetic

**Bio-Operational Triage Engine** — personal infrastructure management for high-performance engineers.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-managed-blueviolet?logo=astral&logoColor=white)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://docs.astral.sh/ruff/)
[![mypy: strict](https://img.shields.io/badge/mypy-strict-blue)](https://mypy.readthedocs.io/)
[![TypeScript: strict](https://img.shields.io/badge/typescript-strict-blue?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Version](https://img.shields.io/badge/version-v1.8.0-blue)](CHANGELOG.md)

---

## For Reviewers

**Problem:** High-performing engineers instrument everything at work — CI pipelines, on-call runbooks, dashboards — but run their personal systems completely blind. Sleep, domestic logistics, and close relationships accumulate hidden debt with no alerting and no triage list. The only feedback loop is burnout, which fires weeks after the damage is done.

**User:** Jordan is a senior software engineer at a growth-stage startup. He ships 50+ hours a week, has the discipline to build reliable production systems, but has never applied that same observability to himself. By the time he notices something is wrong — sleep tanked, laundry three weeks overdue, a close friend he hasn't spoken to in two weeks — he's already deep in a compounding debt spiral that costs 4–8 hours of recovery flow time to unwind.

**What Kinetic does:** One natural-language check-in per day routes through three specialist AI agents (bio, logistics, relational) and an operational liaison. It returns a prioritized triage list of two or three high-leverage actions — the ones that arrest the most compounding debt — so Jordan can clear them in five minutes and return to flow.

**What it does not do:** Kinetic does not provide calendar integration, push notifications, wearable device sync, social features, payment processing, or native mobile apps. It has no automatic data collection — every data point comes from a user check-in message.

**Technology rationale:** Gemini 2.5 Flash + Instructor enforces typed Pydantic output from the LLM, eliminating JSON parsing fragility. FastAPI + asyncpg targets sub-100ms response on structured data queries. The `DatabaseClient` Protocol abstracts SQLite (local dev, zero config) and PostgreSQL (Render production) behind the same 15-method interface — zero application code changes at deploy time. SSE streaming delivers the Operational Liaison's response token-by-token without WebSocket overhead; `fetch` + `ReadableStream` is used instead of `EventSource` because `EventSource` does not support POST bodies.

**What's next:** The highest-value next feature is passive data ingestion — pulling sleep data from a wearable API (Oura, Whoop) so the system updates without a manual check-in. This tests the core assumption that observability, not discipline, is what's missing. After that: a mobile-native interface so the check-in friction drops from 30 seconds to 10.

**Demo script and presentation reference:** [`docs/DEMO.md`](docs/DEMO.md) · [`docs/PRESENTATION.md`](docs/PRESENTATION.md)

**Video demo:**

[![Kinetic demo video](assets/brand/video-thumbnail.png)](https://www.youtube.com/watch?v=P03BV-CmaG8)

---

## What It Is

High-performing engineers routinely fall into the **High-Performance Trap**: relentless output accumulates hidden personal debt — sleep, logistics, relationships — until a crash forces a reset.

Kinetic is a mission-control dashboard that surfaces that debt before it compounds. You brief it in natural language once a day. It routes your input through three domain agents and an operational liaison, then hands back a prioritized, data-driven triage list so you can clear high-leverage actions in minutes and return to flow.

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
| **Operational Liaison** | Tactical orchestration + executive function | Sequenced action scripts, contact pauses |

The orchestrator aggregates agent outputs into a single `SystemHealthPayload` — one consistent shape the React frontend consumes, regardless of which agents fired.

---

## Stack

**Backend**
- Python 3.12, [uv](https://docs.astral.sh/uv/) for environment + dependency management
- [FastAPI](https://fastapi.tiangolo.com/) · [Pydantic v2](https://docs.pydantic.dev/) · [Instructor](https://python.useinstructor.com/) + [Gemini 2.5 Flash](https://ai.google.dev/)
- [asyncpg](https://magicstack.github.io/asyncpg/) + PostgreSQL (Render) · aiosqlite (local dev fallback)
- mypy strict · ruff · pytest + pytest-cov

**Frontend**
- React 18 · TypeScript strict · [Vite](https://vitejs.dev/) · [react-router-dom](https://reactrouter.com/) (URL-based routing)
- [Vitest](https://vitest.dev/) · [Playwright](https://playwright.dev/) · [@axe-core/playwright](https://github.com/dequelabs/axe-core-npm)
- ESLint flat config (TypeScript-ESLint + jsx-a11y strict) · Prettier

**Deployment**
- [Render](https://render.com/) — `render.yaml` Blueprint deploys API service + static frontend + PostgreSQL in one step

**Tooling**
- [Commitizen](https://commitizen-tools.github.io/commitizen/) SemVer (Conventional Commits)
- pre-commit hooks: ruff, mypy, prettier, conventional-pre-commit

---

## Getting Started

### Prerequisites
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Node.js ≥ 18 + npm
- A [Gemini API key](https://aistudio.google.com/app/apikey)

### Local dev

```bash
# 1. Clone
git clone https://github.com/hirekarl/kinetic.git
cd kinetic

# 2. Python environment
uv sync                       # installs all deps + creates .venv

# 3. Environment variables
cp .env.example .env
# Open .env and set GEMINI_API_KEY=<your key from https://aistudio.google.com/app/apikey>
# Leave DATABASE_URL unset — app uses SQLite for local dev

# 4. Tenant credentials
cp credentials.toml.example credentials.toml
# Generate a bcrypt hash for each tenant password:
uv run python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"
# Paste the hash into credentials.toml under the relevant [tenants.*] block

# 5. Commit hooks (run once)
pre-commit install

# 6. Start the backend
uv run uvicorn kinetic.main:app --reload --port 8000

# 7. Start the frontend (separate terminal)
cd frontend
npm install
npm run dev                   # Vite dev server on :5173, proxies /api → :8000
```

Open `http://localhost:5173` and log in with a tenant defined in `credentials.toml`.

### Running the demo

Log in as the `demo` tenant. If the dashboard is empty, click **Simulate Week** in the top-right header — this inserts five pre-scripted check-ins spanning the past seven days and immediately refreshes the burnout trend chart and weekly digest, giving you a fully-populated dashboard without any manual check-ins.

### Running tests

```bash
# Python — unit + integration (SQLite, no external services)
uv run pytest

# Python — PostgreSQL integration tests (requires a running PostgreSQL instance)
DATABASE_URL=postgresql://user:pass@localhost/kinetic uv run pytest tests/integration/test_postgres_client.py -v

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
| Sprint 1 | Agent logic — all three agents + orchestrator | `v0.2.0` | ✅ Released |
| Sprint 2 | LLM parsing layer — Gemini + Instructor end-to-end | `v0.3.0` | ✅ Released |
| Sprint 3 | Frontend core — ChatPanel + Dashboard components | `v0.4.0` | ✅ Released |
| Sprint 4 | Integration + ROI + Persistence + Liaison | `v0.5.0` | ✅ Released |
| Sprint 5 | Behavioral memory — SQLite patterns + profile panel | `v0.6.0` | ✅ Released |
| Sprint 6 | Polish + demo prep — onboarding, a11y, empty states | `v1.0.0` | ✅ Released |
| Sprint 6b | Dashboard interactivity + liaison hardening | `v1.1.0` | ✅ Released |
| Sprint 7 | Agent dispatch log — collapsible multi-agent routing panel | `v1.2.0` | ✅ Released |
| Sprint 8 | Multi-tenant auth — JWT sessions, bcrypt credentials, per-tenant DB isolation | `v1.3.0` | ✅ Released |
| Sprint 9 | PostgreSQL migration — asyncpg dual-mode DB layer + Render Blueprint | `v1.4.0` | ✅ Released |
| Sprint 10 | Streaming responses — SSE token streaming, in-progress chat bubble | `v1.5.0` | ✅ Released |
| Sprint 11 | Burnout trend chart — 14-day SVG polyline in Bio card | `v1.6.0` | ✅ Released |
| Sprint 12 | Weekly digest — Gemini prose summary card with 6h cache + refresh | `v1.7.0` | ✅ Released |
| Sprint 13 | Demo polish — mobile layout, Simulate Week, landing page, brand assets, SEO metadata, PWA manifest, live deploy | `v1.8.0` | 🔄 In progress |

**Demo deadline:** 2026-05-06 · **MVP deadline:** 2026-05-06

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

**Render (production):** `render.yaml` is a [Render Blueprint](https://render.com/docs/blueprint-spec) that provisions the full stack in one click — Python API service, React static site, and a managed PostgreSQL database (basic-256mb). After deploying:

1. Upload `credentials.toml` as a Secret File at `/etc/secrets/credentials.toml`
2. Set `GEMINI_API_KEY` in the API service environment
3. Set `FRONTEND_URL` (API service) and `VITE_API_BASE_URL` (frontend service) to each other's Render URLs
4. Redeploy the frontend so Vite bakes `VITE_API_BASE_URL` in at build time

`DATABASE_URL` is wired automatically from the managed database — no manual configuration needed.

**Local dev:** backend on `:8000`, frontend on `:5173` (Vite proxies `/api` → `:8000`). SQLite is used by default when `DATABASE_URL` is absent. See [Getting Started](#getting-started) above.

---

## Author

**Karl Johnson** · [hirekarl@proton.me](mailto:hirekarl@proton.me)

Built for the [Pursuit](https://www.pursuit.org/) AI-Native L1 Capstone.
