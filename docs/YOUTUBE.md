# YouTube Video Metadata

## Title

Kinetic — Personal Infrastructure for Engineers (AI-Powered Triage Demo)

## Description

Engineers instrument everything at work — dashboards, alerts, runbooks. But they run their personal infrastructure completely blind.

Kinetic is a personal infrastructure management system for high-performance engineers. One natural-language check-in a day. Three specialist AI agents run in parallel — Bio Archivist, Logistics Fixer, Relational Diplomat. One prioritized triage list comes back: the 2–3 actions that stop the most accumulating debt right now.

**What's in this demo:**
- Natural-language check-in across biology, logistics, and relationships in a single message
- Structured LLM parsing via Gemini 2.5 Flash + Instructor → typed Pydantic models
- Lead orchestrator routing three agents in parallel; responses stream over server-sent events
- Burnout score computed from a 7-day weighted sleep trend
- Behavioral pattern detection: Gemini identifies recurring patterns from accumulated history
- Cross-domain triage list ranked 1–10; completing a task re-ranks in real time
- Weekly Digest: a separate Gemini call summarizing the week's trajectory, cached for 6 hours
- Full agent dispatch log: every check-in auditable — which agent responded, what it found, when
- 503 error recovery: the last message replays without a page reload
- Responsive layout down to mobile width
- WCAG 2.1 AA accessibility throughout

**Stack:** Gemini 2.5 Flash · Instructor · FastAPI · Pydantic v2 · React 18 · TypeScript · Vite · SQLite / PostgreSQL · Server-Sent Events

Built as part of the Pursuit AI-Native L1 Capstone — 10-day sprint to demo-ready prototype.

GitHub: https://github.com/hirekarl/kinetic

## Tags

AI engineering, personal productivity, AI agents, Gemini API, FastAPI, React, TypeScript, Pydantic, LLM, structured output, Instructor, server-sent events, streaming AI, burnout tracking, personal infrastructure, software engineer productivity, AI demo, capstone project, Pursuit, full stack AI, Python FastAPI, React TypeScript, developer tools, AI triage, multi-agent AI
