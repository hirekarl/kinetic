# Kinetic: Bio-Operational Triage Engine — PRD

### TL;DR

Kinetic is a personal infrastructure management system designed for high-performance engineers like Karl—individuals who routinely fall into the ‘High-Performance Trap’ where relentless output results in hidden technical debt across self-care, household logistics, and relationship maintenance. Leveraging a multi-agent orchestration layer, Kinetic delegates to three specialized agents—Bio-Metric Archivist (sleep/nutrition + burnout forecast), Logistics Fixer (triage of domestic tasks + outsourcing ROI), and Relational Diplomat (connection margin + interaction sprints)—to enable data-driven sustainability and high-velocity professional life.

---

## Goals

### Business Goals

* **Deliver a demo-ready prototype** within 2 weeks for the Pursuit AI-Native L1 capstone.
* **Prove the ROI of automated self-care** by quantifying operational waste and margin gain using agent-driven recommendations and calculations.
* **Establish Kinetic as a replicable framework** for high-performance individuals addressing similar operational challenges.
* **Achieve production-ready code quality** with static typing (mypy), formatting (ruff), and environment management (uv) for fast, reliable iteration.

### User Goals

* **Sustain a high-velocity workflow** without approaching burnout by surfacing actionable personal “system errors” early.
* **Gain at-a-glance visibility** into the health of their personal infrastructure (sleep, logistics, relationships) through unified dashboarding.
* **Reduce decision fatigue** around self-care and domestic logistics by providing prioritized, data-driven action recommendations.
* **Safeguard relationship health** by tracking and supporting intentional connection interventions.

### Non-Goals

* Not a traditional wellness app, fitness tracker, or habit builder.
* Not a social platform or tool for shared/communal household coordination.
* Not attempting full automation of physical tasks—Kinetic surfaces and delegates, but does not execute them directly.

---

## User Stories

### Persona 1 — The Overachiever Engineer (primary: Karl)

* As an overachiever, I want to check my burnout forecast before starting a work sprint, so that I can safely scale my commitments.
* As an overachiever, I want to receive a logistics alert when domestic tasks (e.g., laundry) hit a critical threshold, so that I can schedule high-ROI outsourcing or allocate attention before it impacts my bandwidth.
* As an overachiever, I want to get a relational nudge when my connection margin is in the red, so I can schedule time with friends or family before relationships degrade.
* As an overachiever, I want a single dashboard summarizing overall system health, so I can triage quickly and make informed tradeoffs in real-time.
* As an overachiever, I want the system to suggest concrete, time-bounded actions, so that I don’t waste cognitive resources on micro-decisions.

### Persona 2 — Pursuit Fellowship Reviewer

* As a reviewer, I want to see each specialized agent’s output distinctly, so I can evaluate if the system is well-architected and modular.
* As a reviewer, I want evidence (quantitative or qualitative) of margin gained through Kinetic, so I can judge the impact and ROI of the solution.
* As a reviewer, I want clear documentation and surface area for agent orchestration logic, so I can assess extensibility and future potential.
* As a reviewer, I want to see error states and intentional empty states, so I can validate the maturity of the front-end experience.

---

## Functional Requirements

* **Lead Orchestrator (Priority: P0)**
  * Orchestrates input delegation to agent modules and aggregates overall system health status.
* **Bio-Metric Archivist (Priority: P0)**
  * Allows manual input of daily sleep and nutrition data.
  * Calculates and surfaces a burnout score and forecast based on recent inputs.
* **Logistics Fixer (Priority: P0)**
  * Handles a configurable task list of domestic logistics (laundry, groceries, cleaning, etc.).
  * Flags criticality thresholds (e.g., laundry overdue for 2 days) and triggers outsourcing research (e.g., best laundry pickup options).
* **Relational Diplomat (Priority: P0)**
  * Accepts manual “vibe check” inputs for relationship health.
  * Calculates connection margin and recommends actionable interaction sprints (e.g., call a friend, schedule dinner).
* **Dashboard & ROI Calculator (Priority: P1)**
  * Interactive, at-a-glance dashboard visualizing state changes and agent outputs.
  * ROI calculator quantifying time/margin recovered through agent suggestions vs. baseline.
* **Stretch MVP Features (Priority: P2)**
  * Persistent historical state storage and retrieval.
  * Visualization of burnout trends over time.
  * Additional dashboard modules (e.g., agent logs/history).

---

## User Experience

**Entry Point & First-Time User Experience**

Entry Point & First-Time User Experience

* Users land on a split-panel mission-control UI: a conversational chat panel on the left (primary input) and a live-updating dashboard panel on the right (primary output).
* Chat panel: users brief Kinetic in natural language (e.g., "Slept 5 hours, ate okay, feeling disconnected from Marcus"). The chat replaces the previous form-based daily check-in—natural-language messages are the canonical input mechanism.
* LLM parsing layer: an NLP parsing layer (LLM) sits between chat input and the orchestrator, converting user messages into structured inputs routed to the Bio-Metric Archivist, Logistics Fixer, and Relational Diplomat.
* Dashboard panel: as the orchestrator processes parsed inputs, agent status cards and a prioritized triage list update in real time; streaming responses and status lights indicate processing and partial results.
* First-time onboarding frames Kinetic as “personal infrastructure,” emphasizing rigorous, data-centric triage over life-coaching; micro-tutorials (1-screen each, skippable) explain the split-panel chat-first workflow and agent roles.

**Core Experience**

Core Experience

* Step 1: User briefs Kinetic via the left-hand chat panel: they type or paste a short natural-language status (sleep, nutrition, vibe checks, urgent logistics). Minimal friction: quick message entry, conversational affordances (suggested prompts).
* LLM parsing layer: incoming chat messages are parsed by the LLM into structured fields (sleep hours, nutrition quality, relationship vibe, task mentions) which the lead orchestrator consumes.
* Step 2: Lead Orchestrator processes parsed inputs: validates structured data, routes fields to relevant agents, and coordinates streaming responses. Loading and processing states are surfaced via dashboard status lights.
* Step 3: Agents surface status on the right-hand dashboard panel. Bio-Metric Archivist: burnout status (green/yellow/red) and brief forecast. Logistics Fixer: urgent logistics highlighted (e.g., "Laundry overdue: 2d") with suggested high-leverage next actions (stubbed vendor options in demo). Relational Diplomat: connection margin score and suggested interaction sprints.
* Step 4: Prioritized triage list compiles suggested actions on the dashboard. Actions stream in as agents respond; users can mark items completed or snoozed directly from the dashboard.
* Step 5: ROI summary and trend quick-glance show daily/weekly time and margin recovered, plus burnout risk delta. Dashboard updates continuously as new chat messages arrive and are parsed.

**Advanced Features & Edge Cases**

* Power users can access trendlines for burnout and margin.
* On logistics outsourcing triggers, surface vendor options via API/search (e.g., TaskRabbit).
* Empty/default states have calm, non-alarming messaging (e.g., “You’re all green!” vs blank).
* Error-handling: if an agent fails, fallback to basic status and actionable guidance, with clear flag for troubleshooting.
* System designed for single-user, so robust error messages for missing or malformed inputs, not multi-user conflicts.

**UI/UX Highlights**

* Color-coded agent status indicators (green/yellow/red) styled after production status dashboards.
* Minimalist, non-judgmental copy (“System health degraded” not “You failed to sleep”).
* Responsive, mobile-friendly layout; legible at a glance.
* Accessibility: high color contrast, semantic HTML elements, logical tab order.

---

## Narrative

It’s 9pm on a Wednesday. Karl, a high-performing engineer, is deep in a late-night build sprint—his code is flowing, productivity at its peak. Yet, running quietly alongside his IDE, Kinetic's dashboard slides a subtle alert: yellow warning. A glance reveals that sleep debt is quietly accumulating; the laundry task crossed a critical threshold two days prior, and his connection margin with a close friend has languished in the red for 11 days.

Prior to Kinetic, Karl’s only feedback loop was burnout—he’d crash, relationships would suffer, chores would snowball, professional progress would halt. Now, instead of becoming a crisis, he’s handed a prioritized triage list: order laundry pickup tonight (15 minutes, reclaim 2 weekend hours), send a 30-second text to a friend to schedule a call, and commit to a hard stop at 11pm to preserve tomorrow’s output.

Returning to his sprint after clearing three high-leverage actions in under five minutes, Karl doesn’t feel policed or guilted by his tools. Instead, he’s simply operating his own life with the same data-driven clarity and operational rigor he brings to his servers. Kinetic ensures his momentum remains unbroken, his baselines protected, and his growth sustainable—demonstrating that elite professional output and resilient personal maintenance need not be at odds.

---

## Success Metrics

* **User-Centric Metrics**

  * **Daily check-in completion rate:** Percentage of days with completed check-in.
  * **Time-to-triage:** Average time between a flagged item and user action.
  * **Self-reported burnout score trend:** Downward movement or stabilization in burnout over two weeks.

* **Business Metrics (Capstone/Project)**

  * **Demo readiness:** Successful demonstration of all agent outputs at the Pursuit L1 review.
  * **Unified orchestrated response:** System correctly routes and aggregates all three agent functions in a live demo.
  * **Quantifiable ROI:** Visible, explainable ROI metrics for time/margin recovery.

* **Technical Metrics**

  * **Backend type-checking and linting:** mypy and ruff report zero errors/warnings.
  * **Frontend state accuracy:** Real-time rendering for all agent outputs and state changes.
  * **API latency:** All agent responses within 2 seconds.

* **Tracking Plan**

  * Log every check-in submission.
  * Log every agent “flagged” event.
  * Log user actions on triage items (completed/snoozed).
  * Log each time the ROI calculator is rendered.
  * Track dashboard views and navigation events.

---

## Technical Considerations

Technical Needs

## Technical Considerations

Technical Needs

### Core Data Model

The system uses a single unified CheckInPayload Pydantic model parsed from the user’s conversational input via Google Gemini 2.5 Flash + Instructor in one LLM call per check-in.

SystemHealthPayload (output model): Each agent returns its own typed status model — `BioStatus`, `LogisticsStatus`, and `RelationalStatus` — and the lead orchestrator normalizes these into a single `SystemHealthPayload` that is sent to the frontend. SystemHealthPayload contains an `overall_status` field ("green"/"yellow"/"red") computed by the orchestrator based on aggregate agent outputs; optional `bio`, `logistics`, and `relational` sub-models (each typed as `BioStatus`, `LogisticsStatus`, and `RelationalStatus`, respectively) which are `None` if that agent was not triggered; a flat `triage_items` list aggregated across all agents and rendered as a unified priority queue on the dashboard; and an optional `roi_summary` field that remains `None` until sufficient data exists (this maps directly to an intentional empty state on the frontend).

The orchestrator owns the `overall_status` computation logic because it has visibility across all three agents — no single agent determines system health alone. By centralizing aggregation and status computation in the orchestrator, the React frontend remains simple and agent-agnostic: it consumes one consistent state object regardless of which agents fired. Adding a future fourth agent requires only orchestrator and agent updates (no frontend changes) since the SystemHealthPayload shape and rendering logic remain stable.

**Structure:** `CheckInPayload` contains three optional nested sub-models — `BioInput`, `LogisticsInput`, and `RelationalInput` — each typed to the fields required by their respective agent. All sub-model fields are optional (default `None`), so if the user’s message does not reference a domain (e.g., no sleep mention), that sub-model is `None` and the corresponding agent is skipped gracefully rather than causing a failure.

**Orchestration routing:** The lead orchestrator inspects the parsed payload and routes accordingly: `if payload.bio is not None` → route to Bio-Metric Archivist; `if payload.logistics is not None` → route to Logistics Fixer; `if payload.relational is not None` → route to Relational Diplomat.

**Benefits:** This pattern keeps LLM call count to one per check-in, preserves strict mypy compliance (Pydantic models double as typed contracts), and ensures a clean separation between parsing logic and agent implementation so agents receive well-typed, validated inputs without duplicative parsing or extra LLM calls.

* Backend: Python project using uv for environments, strict mypy type annotations, ruff for linting/formatting.
* LLM parsing layer: conversational interface requires integration with Google Gemini 2.5 Flash via the Gemini API as the LLM provider to parse free-text chat into structured agent inputs; the LLM sits between chat input and the orchestrator. Instructor is used to enforce structured outputs from Gemini 2.5 Flash: Instructor wraps the Gemini API call and uses Pydantic models to validate and type the LLM response, ensuring the orchestrator always receives a clean, typed payload for agent routing. Pydantic models defined for Instructor double as type definitions for the orchestrator input contracts, keeping the full pipeline—from chat input to agent routing—consistent with the project's strict mypy enforcement. (Existing Gemini API setup from prior projects is available, making this a low-friction integration.)
* Orchestration layer: Lead orchestrator, pluggable agents for health, logistics, and relationships.
* Frontend: React UI focused on split-panel state visualization (chat + live dashboard), rapid input, and calming empty/error states.
* API endpoints per agent and for orchestrator aggregation.

### Integration Points

Integration Points

### Integration Points

Integration Points

* LLM API integration: Google Gemini 2.5 Flash via the Gemini API (Google) as the first-class integration for parsing conversational input into structured fields for agent routing.
* Logistics Fixer surfaces vendor options/payloads via external APIs (e.g., TaskRabbit, local laundry services). For the demo, these external calls should be stubbed with static responses; live API wiring is deferred to the MVP stretch goal.
* ROI module may reference or benchmark against standard “outsider” time value APIs/calculators if desired.

### Data Storage & Privacy

* For demo: Store state locally or in a lightweight file-based DB, with clear wipe/reseed options.
* For MVP: Optionally persist historical data for trend analysis.
* All data is single-user, fully private, with no login or auth for demo; only basic auth for stretch MVP if time allows.

### Scalability & Performance

* Designed for single-user, local performance.
* Codebase/architecture should allow extension to multi-user, multi-device with future refactors.
* Target API response <2 seconds agent-to-dashboard, even if agents run async logic underneath.

### Potential Challenges

* Orchestration latency if chaining async agent tasks.
* Ensuring clean architectural separation between agent logic and dashboard state.
* Error handling for agent failures, input validation, and partial data submissions.
* Keeping the experience “infrastructure-like” without straying into generic wellness app territory.

---

## Milestones & Sequencing

Total Timeline: 10 daysTeam: 1 person (Karl)Project Size: Medium (compressed to 10 days)

### Project Estimate

* Medium: 2–4 weeks (with timeboxing and high-velocity solo builder, targeted 10 days).

### Team Size & Composition

* Extra-small: 1 person (Product, Engineering, UI/UX all handled by Karl).

### Suggested Phases

Phase 1: Backend Scaffolding (Days 1–2)

* Deliverables: Python project scaffolding with uv, mypy, ruff. Agent interfaces and lead orchestrator skeleton. Stubbed logic for all three agents. Dependencies: None.

Phase 2: Agent Logic + LLM Parsing Layer (Days 3–6)

* Deliverables: Fully-implemented Bio-Metric Archivist with burnout forecast. Logistics Fixer criticality/outsourcing logic (with demo stubs for external vendors). Relational Diplomat vibe check + connection margin computation. LLM parsing layer integration that converts chat messages into structured agent inputs. Dependencies: Phase 1 completion.

Phase 3: Frontend & Integration (Days 7–9)

* Deliverables: Initial React split-panel UI with chat input (left) and live-updating dashboard (right). Visualizations for each agent’s output and overall system health. Backend–frontend API connections. Working ROI calculator view. Streaming updates from orchestrator and LLM parsing integration. Dependencies: Backend endpoints stable; agent logic and LLM layer implemented.

Phase 4: Polish & Demo Prep (Day 10)

* Deliverables: Error-handling, empty states, onboarding flow, and demo script/live system walkthrough. If time: persistent state, history/trend views and other stretch items.

Critical Milestones:

* Day 8: Demo-ready prototype (all agents working end-to-end with chat parsing and dashboard streaming).
* Day 10: Fully functional MVP, including polish and stretch goals as time allows.