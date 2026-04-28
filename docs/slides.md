---
marp: true
theme: dracula
paginate: true
_class: lead
---

# Kinetic
### Bio-Operational Triage Engine
**Personal Infrastructure for High-Performance Engineers**

---

## The Problem: Jordan
- **Senior SWE:** Optimized for output, ships 50+ hours/week.
- **The Blind Spot:** Instruments CI/CD and on-call, but runs personal life on "instinct."
- **The Debt Spiral:** Sleep deficit → cognitive decline → domestic backlog → relational drift.
- **The Only Alert:** Burnout. (And burnout only fires after the crash.)

---

## The Root Cause: Observability Gap
> "You're operating critical infrastructure without a dashboard."

- No SLO for sleep.
- No alerting on laundry thresholds.
- No triage list for connection margin.
- **Kinetic provides the observability layer Jordan is missing.**

---

## The Architecture

### Backend
- **Gemini 2.5 Flash + Instructor**
- FastAPI / Pydantic v2
- SQLite (Local) / Postgres (Prod)

### Frontend
- **React 18 / TypeScript**
- SSE (Server-Sent Events)
- Tailwind CSS / Sparklines

---

## Live Check-In Logic

1. **Natural Language Input:** "Slept 5h, ate okay, feeling disconnected from Marcus."
2. **Structured Extraction:** Instructor enforces typed `CheckInPayload`.
3. **Agent Routing:**
   - `BioArchivist` (Burnout Forecast)
   - `LogisticsFixer` (Outsourcing ROI)
   - `RelationalDiplomat` (Interaction Sprints)
4. **Unified Triage:** Sorted by compounding debt risk.

---

## [DEMO] Live Walkthrough
1. **Onboarding:** Keyboard-navigable & A11y compliant.
2. **Behavioral History:** Pattern detection (e.g., `chronic_sleep_deficit`).
3. **Live Stream:** Token-by-token SSE response.
4. **Performance Yield:** Quantifying the ROI of inaction.

---

## Summary & ROI
- **Efficiency:** < 5 mins/day for triage.
- **Leverage:** 3+ high-leverage actions surfaced weekly.
- **Prevention:** Avoids 4–8h "recovery events" monthly.

**Kinetic: Sustaining high velocity through data-driven triage.**
