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
    routes.py              FastAPI APIRouter (GET /api/digest, POST /api/checkin, POST /api/checkin/stream, GET /api/history, PATCH /api/tasks/{task_name}/complete, POST /api/debug/reset, POST /api/demo/simulate); all routes require get_current_tenant; /stream returns EventSourceResponse via sse-starlette; /digest returns DigestResponse (cached 6h, force=bool param); /demo/simulate is 403-gated to demo tenant only
  db/
    base.py                DatabaseClient Protocol — 15-method shared interface satisfied by both SqliteClient and PostgresClient
    sqlite_client.py       SQLite persistence: check-ins, bio metrics, tasks, vibes, behavioral profiles, contact_pauses; get_behavioral_summary(), get_behavioral_profiles(), upsert_behavioral_profile(), upsert_contact_pause(), get_active_pauses(), get_burnout_series(), insert_checkin_at()
    postgres_client.py     asyncpg PostgreSQL client: same 15-method interface as SqliteClient; per-tenant row isolation via tenant column; _migrate() for idempotent DDL; get_burnout_series(), insert_checkin_at()
  services/
    __init__.py            package init
    pattern_detector.py    detect_and_update_patterns(): rate-limited Gemini pattern synthesis, fires as background asyncio task
    digest_generator.py    generate_digest(): 6h in-memory cache per tenant; empty-history guard; Gemini prose summary; exception-safe (returns [DIGEST ERROR] string on failure)
    simulate.py            simulate_week(): inserts 5 pre-scripted check-in snapshots with timestamps spread across 7 historical days for demo population

tests/
  conftest.py              shared fixtures (sample payloads, health objects)
  unit/test_models.py      model validation tests
  unit/test_main.py        startup warning / lifespan tests; pool create + close lifecycle (AsyncMock)
  unit/test_auth.py        auth utility tests: verify_password, JWT round-trip, expired/tampered tokens, FastAPI dependency behavior
  unit/test_lead_db.py     get_db() isolation tests: default path, named tenant path, client caching, pool-mode branch
  unit/test_db_protocol.py DatabaseClient Protocol completeness: all 15 method names, isinstance check against SqliteClient
  unit/test_simulate_route.py 7 tests for POST /api/demo/simulate: 401 no auth, 403 non-demo tenant, 200 shape, service called, 5 rows inserted, timestamps historical, CheckInPayload type verified
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
  types/index.ts           TypeScript interfaces mirroring Python output models; includes AuthUser, ContactPauseDirective, StreamDonePayload, DigestResponse
  App.tsx                  split-panel root component; auth-gated (loading spinner → LoginScreen → dashboard); onboarding gate via localStorage; Sign Out + display name in header; uses streamCheckin with accumulatedRef + streamingContent state; digestData/digestLoading/digestRefreshing state + handleRefreshDigest callback; isSimulating state + handleSimulateWeek; "Simulate Week" button (demo tenant only, aria-label toggles during loading); mobile-responsive layout (flex-col lg:flex-row, h-[45vh] lg:h-auto, p-4 md:p-8)
  components/LoginScreen.tsx  full-viewport login card; labeled inputs; role="alert" error display; auto-focus on mount; loading state support
  components/OnboardingModal.tsx  3-screen first-visit tutorial; localStorage persistence; focus trap + Escape key
  components/ChatPanel/    natural-language input + streaming display; streamingContent prop drives in-progress bubble with blinking cursor
  components/Dashboard/    status cards, triage list, ROI summary, behavioral profile panel, sleep sparkline, burnout trend chart, weekly digest card, agent dispatch log
    SleepSparkline.tsx     pure SVG polyline sparkline; aria-hidden; amber/emerald stroke from declining prop; null for < 2 points
    BurnoutTrendChart.tsx  SVG polyline chart for 14-day burnout series; red/amber/emerald stroke from linear regression slope; aria-hidden + sr-only label; null for < 2 points
    WeeklyDigestCard.tsx   collapsible "Weekly Review" disclosure; prose summary paragraph; "Generated X minutes ago" relative timestamp; Refresh button with spinner; loading skeleton (role="status"); [DIGEST ERROR] error block; no-data empty state
    AgentDispatchLog.tsx   collapsible agent routing history; per-entry expandable agent summaries + responding_agent badge
  utils/
    agentLog.ts            buildAgentLogEntry(): derives AgentLogEntry from SystemHealthPayload + message + timestamp
  hooks/
    useAuth.ts             useAuth(): user/token/isLoading state; lazy isLoading init prevents flash-of-LoginScreen; localStorage JWT persistence; mount-time fetchMe validation; login/logout actions
  api/
    client.ts              fetchCheckin, fetchHistory, completeTask, fetchDigest, simulateWeek (all accept optional token); login, fetchMe, logout; streamCheckin() SSE client with manual ReadableStream parsing and fetchCheckin fallback; authHeaders() helper
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
| Sprint 12 | `v1.7.0` | Weekly Digest | ✅ |
| Sprint 13 | `v1.8.0` | Demo Polish + Shareable Deploy | 🔄 |

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
SECRET_KEY=your-32-byte-hex-string-here  # generate: python -c "import secrets; print(secrets.token_hex(32))"
CREDENTIALS_PATH=./credentials.toml      # optional; defaults to ./credentials.toml
DATABASE_URL=postgresql://user:pass@host/db  # optional; if set, app uses PostgreSQL (Render injects this automatically); omit for SQLite local dev
SQLITE_DB_PATH=./kinetic.db              # optional; SQLite path for the "default" tenant; named tenants use kinetic_{tenant}.db
FRONTEND_URL=https://your-frontend.onrender.com  # optional; added to CORS allow_origins at startup (Render production only)
```

The app reads this via `python-dotenv`. The `.gitignore` already excludes `.env`. Copy `credentials.toml.example` to `credentials.toml` and fill in real bcrypt hashes (never commit it).

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
- `SystemHealthPayload` — returned by orchestrator, consumed by frontend; one consistent shape regardless of which agents fired; includes `behavioral_summary: BehavioralSummary | None`, `responding_agent: str | None`, `active_pauses: list[ContactPause]`
- Sub-models: `BioStatus`, `LogisticsStatus`, `RelationalStatus`, `TriageItem`, `ROISummary`, `BioTrend` (includes `sleep_series: list[float]` — per-day hours oldest→newest; `burnout_series: list[float]` — per-entry burnout 0-100 oldest→newest), `RecurringTask`, `RelationalDrift`, `BehavioralSummary`, `BehavioralProfile`, `ContactPause`
- Standalone digest model: `DigestResponse` (in `models/outputs.py`) — `summary: str`, `generated_at: datetime`; returned by `GET /api/digest`; TS mirror: `DigestResponse { summary: string; generated_at: string }`
- Internal agent model: `LiaisonResponse` (in `agents/operational_liaison.py`) — `text: str`, `responding_agent: RespondingAgent`, `contact_pauses: list[ContactPauseDirective]`
- Internal streaming metadata: `LiaisonMetadata` (in `agents/operational_liaison.py`) — lightweight post-stream extraction: `responding_agent`, `contact_pauses`, `task_completions`
- Frontend streaming contract: `StreamDonePayload` (in `frontend/src/types/index.ts`) — `responding_agent`, `contact_pauses: ContactPauseDirective[]`, `task_completions`, `active_pauses`, `behavioral_profiles`, `behavioral_summary`; `ContactPauseDirective` mirrors Python model

---

## Accessibility Standards

All UI must pass WCAG 2.1 AA. The `eslint-plugin-jsx-a11y` strict config and `@axe-core/playwright` e2e audits enforce this automatically.
