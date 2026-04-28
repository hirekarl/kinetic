# Kinetic — GEMINI.md

**Author:** Karl Johnson <hirekarl@proton.me>
**Project:** Bio-Operational Triage Engine — Pursuit AI-Native L1 Capstone
**Timeline:** 10-day sprint to demo-ready prototype
**Stack:** Python 3.12 / uv / FastAPI / Pydantic v2 / Gemini 2.5 Flash + Instructor · React 18 / TypeScript / Vite / Vitest / Playwright

---

## STARTUP RITUAL — Run This Before Any Shell Commands

**This step is mandatory.** Before issuing any shell commands in this session, detect the execution environment and apply the correct shell profile. Gemini running in a Windows environment is known to emit bash-style syntax that breaks in PowerShell — this ritual prevents that.

### Step 1: Detect OS

Run these checks in order and stop at the first match:

| Check | Result |
|-------|--------|
| Does `$env:OS` equal `Windows_NT`? | **Windows** |
| Does `/System/Library/CoreServices/` exist? | **macOS** |
| Does `/etc/os-release` exist? | **Linux** |

### Step 2: Detect Shell

| Check | Result |
|-------|--------|
| Does `$PSVersionTable` resolve without error? | **PowerShell** |
| Is `$ZSH_VERSION` set? | **Zsh** |
| Is `$BASH_VERSION` set? | **Bash** |

### Step 3: Apply Shell Profile

Use **only** the syntax column matching your detected shell for the entire session:

| Operation | Bash / Zsh (macOS/Linux) | PowerShell (Windows) |
|-----------|--------------------------|----------------------|
| Set env var | `export KEY=value` | `$env:KEY = "value"` |
| Activate virtualenv | `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` |
| Run via uv | `uv run pytest` | `uv run pytest` _(same — uv is cross-OS)_ |
| Path separator | `/` | `\` or `/` _(both work in PS 7+)_ |
| Chain commands | `cmd1 && cmd2` | `cmd1; cmd2` _(PS 5)_ / `&&` _(PS 7+)_ |
| Read file | `cat file.txt` | `Get-Content file.txt` |
| List directory | `ls -la` | `Get-ChildItem` |
| Set executable | `chmod +x script.sh` | _(not applicable on Windows)_ |

**Never use `source`, `export`, or `&&` chaining in a PowerShell session.**
**Never use `$env:` or `Get-Content` in a bash/zsh session.**

Confirm your detected profile in a comment before your first tool call, e.g.:
```
# Environment: macOS / Zsh — using bash-style syntax
```

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
  main.py                  FastAPI app, CORS config, router mounts (api + auth); lifespan: warnings for GEMINI_API_KEY + SECRET_KEY, asyncpg pool create/close when DATABASE_URL set
  auth.py                  TenantConfig + CurrentUser models; load_credentials(), verify_password(), create_access_token(), decode_access_token(); get_current_user() + get_current_tenant() FastAPI dependencies
  models/
    inputs.py              CheckInPayload + sub-models (canonical input contracts)
    outputs.py             SystemHealthPayload + sub-models (canonical output contracts)
  agents/
    base.py                Agent Protocol + AgentResult base class
    bio_archivist.py       sleep/nutrition tracking + burnout forecast
    logistics_fixer.py     task triage + outsourcing ROI
    relational_diplomat.py connection margin + interaction sprints
    operational_liaison.py Instructor-based structured router; LiaisonResponse + LiaisonMetadata models; _build_prompt_parts() shared helper; stream_text() async generator (raw token streaming via google-genai); extract_metadata() lightweight post-stream Instructor call; _METADATA_KEYWORDS keyword guard
  orchestrator/
    lead.py                routing logic + status aggregation + behavioral memory wiring + contact pause persistence + triage filtering; dual-mode get_db(tenant): PostgresClient when _pg_pool set, SqliteClient otherwise; orchestrate_stream() async generator yielding agents/token/done SSE event dicts
  parsing/
    llm_parser.py          Gemini 2.5 Flash + Instructor integration
  api/
    __init__.py            package init
    auth.py                JWT auth endpoints: POST /api/auth/login, GET /api/auth/me, POST /api/auth/logout; LoginRequest + TokenResponse models
    routes.py              FastAPI APIRouter (GET /api/digest, POST /api/checkin, POST /api/checkin/stream, GET /api/history, PATCH /api/tasks/{task_name}/complete, POST /api/debug/reset); all routes require get_current_tenant; /stream returns EventSourceResponse via sse-starlette; /digest returns DigestResponse (cached 6h, force=bool param)
  db/
    base.py                DatabaseClient Protocol — 14-method shared interface satisfied by both SqliteClient and PostgresClient
    sqlite_client.py       SQLite persistence: check-ins, bio metrics, tasks, vibes, behavioral profiles, contact_pauses; get_behavioral_summary(), get_behavioral_profiles(), upsert_behavioral_profile(), upsert_contact_pause(), get_active_pauses(), get_burnout_series()
    postgres_client.py     asyncpg PostgreSQL client: same 14-method interface as SqliteClient; per-tenant row isolation via tenant column; _migrate() for idempotent DDL; get_burnout_series()
  services/
    __init__.py            package init
    pattern_detector.py    detect_and_update_patterns(): rate-limited Gemini pattern synthesis, fires as background asyncio task
    digest_generator.py    generate_digest(): 6h in-memory cache per tenant; empty-history guard; Gemini prose summary; exception-safe (returns [DIGEST ERROR] string on failure)

tests/
  conftest.py              shared fixtures (sample payloads, health objects)
  unit/test_models.py      model validation tests
  unit/test_main.py        startup warning / lifespan tests; pool create + close lifecycle (AsyncMock)
  unit/test_auth.py        auth utility tests: verify_password, JWT round-trip, expired/tampered tokens, FastAPI dependency behavior
  unit/test_lead_db.py     get_db() isolation tests: default path, named tenant path, client caching, pool-mode branch
  unit/test_db_protocol.py DatabaseClient Protocol completeness: all 14 method names, isinstance check against SqliteClient
  unit/test_burnout_series.py 14 tests for get_burnout_series(): empty/single/formula/ordering/days-filter/partial/all-None/perfect-health; Postgres mock; get_behavioral_summary() wiring
  unit/test_digest_generator.py 10 tests for generate_digest(): happy path, cache hit/miss/TTL, force=True bypass+update, empty-data canned response, history-only guard bypass, Gemini exception recovery
  unit/test_digest_route.py 5 tests for GET /api/digest: 200 shape, force=False default, force=True forwarded, 401 without JWT, 503 without API key
  unit/test_streaming.py   17 tests for LiaisonMetadata defaults, stream_text() chunking, extract_metadata() keyword guard + Instructor path + failure fallback, orchestrate_stream() event order + persistence + agent failure recovery + side effects
  unit/                    agent logic, orchestrator, parser tests (Phase 2+)
  integration/test_auth_routes.py  auth endpoint tests: login happy/error paths, me, protected routes
  integration/test_postgres_client.py  29 PostgresClient integration tests; all methods + tenant isolation; skipped without DATABASE_URL
  integration/test_stream_route.py  6 SSE endpoint tests: 400 on empty, 503 on OSError, content-type header, agents/token/done event presence
  integration/             end-to-end API tests (Phase 3+)
  scenarios/               deterministic scenario fixtures for adversarial/multi-turn coverage (Sprint 6b)

frontend/src/
  types/index.ts           TypeScript interfaces mirroring Python output models; includes AuthUser, ContactPauseDirective, StreamDonePayload
  App.tsx                  split-panel root component; auth-gated (loading spinner → LoginScreen → dashboard); onboarding gate via localStorage; Sign Out + display name in header; uses streamCheckin with accumulatedRef + streamingContent state
  components/LoginScreen.tsx  full-viewport login card; labeled inputs; role="alert" error display; auto-focus on mount; loading state support
  components/OnboardingModal.tsx  3-screen first-visit tutorial; localStorage persistence; focus trap + Escape key
  components/ChatPanel/    natural-language input + streaming display; streamingContent prop drives in-progress bubble with blinking cursor
  components/Dashboard/    status cards, triage list, ROI summary, behavioral profile panel, sleep sparkline, burnout trend chart, agent dispatch log
    SleepSparkline.tsx     pure SVG polyline sparkline; aria-hidden; amber/emerald stroke from declining prop; null for < 2 points
    BurnoutTrendChart.tsx  SVG polyline chart for 14-day burnout series; red/amber/emerald stroke from linear regression slope; aria-hidden + sr-only label; null for < 2 points
    AgentDispatchLog.tsx   collapsible agent routing history; per-entry expandable agent summaries + responding_agent badge
  utils/
    agentLog.ts            buildAgentLogEntry(): derives AgentLogEntry from SystemHealthPayload + message + timestamp
  hooks/
    useAuth.ts             useAuth(): user/token/isLoading state; lazy isLoading init prevents flash-of-LoginScreen; localStorage JWT persistence; mount-time fetchMe validation; login/logout actions
  api/
    client.ts              fetchCheckin, fetchHistory, completeTask (all accept optional token); login, fetchMe, logout; streamCheckin() SSE client with manual ReadableStream parsing and fetchCheckin fallback; authHeaders() helper
  test/setup.ts            Vitest + @testing-library/jest-dom bootstrap
  e2e/                     Playwright + axe-core specs: auth.spec.ts, app.spec.ts, onboarding.spec.ts, a11y-audit.spec.ts
```

---

## Roadmap

`ROADMAP.md` at the repo root tracks sprint-by-sprint progress against the PRD's four phases. Each sprint targets a version bump. The `/docs-keeper` agent owns this file — check it off as tasks complete and flip sprint status emoji (⬜ → 🔄 → ✅) at the end of each cycle.

| Sprint | Version | Focus | Status |
|--------|---------|-------|--------|
| Sprint 0 | `v0.1.0` | Bootstrap | ✅ |
| Sprint 1 | `v0.2.0` | Agent Logic | ✅ |
| Sprint 2 | `v0.3.0` | LLM Parsing | ✅ |
| Sprint 3 | `v0.4.0` | Frontend Core | ✅ |
| Sprint 4 | `v0.5.0` | Integration + ROI | ✅ |
| Sprint 5 | `v0.6.0` | Behavioral Memory | ✅ |
| Sprint 6 | `v1.0.0` | Polish + Demo | ✅ |
| Sprint 6b | `v1.1.0` | Dashboard Interactivity + Liaison Hardening | ✅ |
| Sprint 7 | `v1.2.0` | Agent Dispatch Log | ✅ |
| Sprint 8 | `v1.3.0` | Multi-Tenant Auth | ✅ |
| Sprint 9 | `v1.4.0` | PostgreSQL Migration | ✅ |
| Sprint 10 | `v1.5.0` | Streaming Responses | ✅ |
| Sprint 11 | `v1.6.0` | Burnout Trend Chart | ✅ |
| Sprint 12 | `v1.7.0` | Weekly Digest | ⬜ |
| Sprint 13 | `v1.8.0` | Demo Polish + Shareable Deploy | ⬜ |

---

## Dev Commands

All Python commands use `uv run` — no manual venv activation needed.

### Bash / Zsh (macOS / Linux)

```bash
# Environment setup
uv sync
cp .env.example .env   # then fill in GEMINI_API_KEY

# Backend
uv run uvicorn kinetic.main:app --reload --port 8000
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/kinetic --strict

# Frontend (from /frontend)
npm install
npm run dev
npm run test:coverage
npm run lint
npm run e2e

# Pre-commit
pre-commit install
pre-commit run --all-files

# Release ceremony
./scripts/release.sh
```

### PowerShell (Windows)

```powershell
# Environment setup
uv sync
Copy-Item .env.example .env   # then fill in GEMINI_API_KEY

# Backend
uv run uvicorn kinetic.main:app --reload --port 8000
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/kinetic --strict

# Frontend (from /frontend)
npm install
npm run dev
npm run test:coverage
npm run lint
npm run e2e

# Pre-commit
pre-commit install
pre-commit run --all-files

# Release ceremony (use Git Bash or WSL on Windows)
# ./scripts/release.sh
# Or manually: uv run cz bump --changelog; git push; git push --tags
```

---

## Environment Variables

Create `.env` at the project root (never commit it):

```
GEMINI_API_KEY=your_key_here
SECRET_KEY=your-32-byte-hex-string-here  # generate: python -c "import secrets; print(secrets.token_hex(32))"
CREDENTIALS_PATH=./credentials.toml      # optional; defaults to ./credentials.toml
DATABASE_URL=postgresql://user:pass@host/db  # optional; if set, app uses PostgreSQL (Render injects this automatically); omit for SQLite local dev
SQLITE_DB_PATH=./kinetic.db              # optional; SQLite path for the "default" tenant; named tenants use kinetic_{tenant}.db
FRONTEND_URL=https://your-frontend.onrender.com  # optional; added to CORS allow_origins at startup (Render production only)
```

The app reads this via `python-dotenv`. The `.gitignore` already excludes `.env`. Copy `credentials.toml.example` to `credentials.toml` and fill in real bcrypt hashes (never commit it).

---

## Running Locally (MVP Target)

The MVP demos locally. Two terminals:

```bash
# Terminal 1 — backend
uv run uvicorn kinetic.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api/*` to `:8000` automatically.

---

## SemVer & Release Ceremony

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Every commit must use one of:

```
feat:     new feature → bumps MINOR
fix:      bug fix     → bumps PATCH
docs:     docs only   → bumps PATCH
refactor: refactor    → bumps PATCH
test:     tests       → bumps PATCH
chore:    maintenance → bumps PATCH
perf:     performance → bumps PATCH
ci:       CI changes  → bumps PATCH

BREAKING CHANGE: (footer) → bumps MAJOR
```

**To cut a release (macOS/Linux):**
```bash
./scripts/release.sh
```

**To cut a release (Windows — use Git Bash or WSL):**
```bash
bash scripts/release.sh
```

---

## TDD Workflow

Every feature follows **Red → Green → Refactor** strictly:

1. **Red:** Write failing test(s) expressing the acceptance criteria
2. **Green:** Write the minimum implementation to pass the tests
3. **Refactor:** Clean up while keeping tests green

**Quality gates:**
- `pytest` coverage ≥ 80%
- `mypy --strict` passes with zero errors
- `ruff check` passes with zero warnings
- `npm run test:coverage` coverage ≥ 80% on all thresholds
- `npm run lint` passes with zero errors (includes jsx-a11y strict)
- Playwright e2e + axe audits pass (zero WCAG 2.1 AA violations)

---

## Multi-Agent Dev Team

Six specialist agents are available as Claude Code slash commands:

| Command | Agent | Responsibility |
|---------|-------|---------------|
| `/architect` | Architect | Decompose features → design docs + task cards with typed contracts |
| `/backend-dev` | Backend TDD Dev | Write failing Python tests first, then implementation |
| `/frontend-dev` | Frontend TDD Dev | Write failing Vitest/Playwright tests first, then React/TS implementation |
| `/qa-reviewer` | QA Reviewer | Validate test quality, coverage, integration scenarios |
| `/security-reviewer` | Security Reviewer | bandit/pip-audit/npm audit, OWASP Top 10, secrets scan |
| `/docs-keeper` | Docs Keeper | Keep CLAUDE.md, GEMINI.md, inline docs, and memory in sync with code |

---

## Pydantic Contracts (Canonical Truth)

The Python models in `src/kinetic/models/` are the single source of truth for data shapes. The TypeScript interfaces in `frontend/src/types/index.ts` mirror them exactly. When changing a Python model, update the TS types in the same PR.

**Input contract:**
- `CheckInPayload` — parsed from user's natural-language message; all sub-models Optional
- Sub-models: `BioInput`, `LogisticsInput`, `RelationalInput`

**Output contract:**
- `SystemHealthPayload` — returned by orchestrator, consumed by frontend; one consistent shape regardless of which agents fired; includes `behavioral_summary: BehavioralSummary | None`, `responding_agent: str | None`, `active_pauses: list[ContactPause]`
- Sub-models: `BioStatus`, `LogisticsStatus`, `RelationalStatus`, `TriageItem`, `ROISummary`, `BioTrend` (includes `sleep_series: list[float]` — per-day hours oldest→newest; `burnout_series: list[float]` — per-entry burnout 0-100 oldest→newest), `RecurringTask`, `RelationalDrift`, `BehavioralSummary`, `BehavioralProfile`, `ContactPause`
- Standalone digest model: `DigestResponse` (in `models/outputs.py`) — `summary: str`, `generated_at: datetime`; returned by `GET /api/digest`; TS mirror: `DigestResponse { summary: string; generated_at: string }`
- Internal agent model: `LiaisonResponse` (in `agents/operational_liaison.py`) — `text: str`, `responding_agent: RespondingAgent`, `contact_pauses: list[ContactPauseDirective]`
- Internal streaming metadata: `LiaisonMetadata` (in `agents/operational_liaison.py`) — lightweight post-stream extraction: `responding_agent`, `contact_pauses`, `task_completions`
- Frontend streaming contract: `StreamDonePayload` (in `frontend/src/types/index.ts`) — `responding_agent`, `contact_pauses: ContactPauseDirective[]`, `task_completions`, `active_pauses`, `behavioral_profiles`, `behavioral_summary`; `ContactPauseDirective` mirrors Python model

---

## Accessibility Standards

All UI must pass WCAG 2.1 AA. The `eslint-plugin-jsx-a11y` strict config and `@axe-core/playwright` e2e audits enforce this automatically.
