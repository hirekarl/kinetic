import { describe, it, expect } from 'vitest';
import { buildAgentLogEntry } from './agentLog';
import type { SystemHealthPayload } from '../types';

function makePayload(overrides: Partial<SystemHealthPayload> = {}): SystemHealthPayload {
  return {
    overall_status: 'green',
    bio: null,
    logistics: null,
    relational: null,
    triage_items: [],
    roi_summary: null,
    liaison_feedback: null,
    responding_agent: null,
    behavioral_profiles: [],
    behavioral_summary: null,
    active_pauses: [],
    ...overrides,
  };
}

describe('buildAgentLogEntry', () => {
  const TIMESTAMP = '2026-04-26T10:30:00.000Z';
  const MESSAGE = 'Slept 5 hours, feeling okay';

  it('returns entry with provided message and timestamp', () => {
    const entry = buildAgentLogEntry(MESSAGE, makePayload(), TIMESTAMP);
    expect(entry.user_message).toBe(MESSAGE);
    expect(entry.timestamp).toBe(TIMESTAMP);
    expect(typeof entry.id).toBe('string');
    expect(entry.id.length).toBeGreaterThan(0);
  });

  it('bio-only payload → agents_fired has 1 entry with domain bio', () => {
    const payload = makePayload({
      bio: {
        status: 'yellow',
        burnout_score: 65,
        forecast: 'Moderate risk at current trajectory',
        sleep_debt_hours: 2.5,
        recommendations: [],
      },
    });
    const entry = buildAgentLogEntry(MESSAGE, payload, TIMESTAMP);
    expect(entry.agents_fired).toHaveLength(1);
    expect(entry.agents_fired[0]!.domain).toBe('bio');
    expect(entry.agents_fired[0]!.status).toBe('yellow');
  });

  it('all-three payload → agents_fired has 3 entries in order bio, logistics, relational', () => {
    const payload = makePayload({
      overall_status: 'yellow',
      bio: {
        status: 'yellow',
        burnout_score: 65,
        forecast: 'Moderate risk',
        sleep_debt_hours: 2.5,
        recommendations: [],
      },
      logistics: {
        status: 'red',
        critical_tasks: ['laundry'],
        tasks_with_steps: [],
        outsourcing_suggestions: [],
        time_to_resolve_minutes: 90,
      },
      relational: {
        status: 'green',
        connection_margin_score: 80,
        at_risk_relationships: [],
        interaction_sprints: [],
      },
    });
    const entry = buildAgentLogEntry(MESSAGE, payload, TIMESTAMP);
    expect(entry.agents_fired).toHaveLength(3);
    expect(entry.agents_fired[0]!.domain).toBe('bio');
    expect(entry.agents_fired[1]!.domain).toBe('logistics');
    expect(entry.agents_fired[2]!.domain).toBe('relational');
  });

  it('none-fired payload (all null) → agents_fired is empty', () => {
    const entry = buildAgentLogEntry(MESSAGE, makePayload(), TIMESTAMP);
    expect(entry.agents_fired).toHaveLength(0);
  });

  it('logistics summary includes critical_tasks count and time_to_resolve_minutes', () => {
    const payload = makePayload({
      logistics: {
        status: 'red',
        critical_tasks: ['laundry', 'taxes'],
        tasks_with_steps: [],
        outsourcing_suggestions: [],
        time_to_resolve_minutes: 120,
      },
    });
    const entry = buildAgentLogEntry(MESSAGE, payload, TIMESTAMP);
    const logisticsFired = entry.agents_fired.find((a) => a.domain === 'logistics');
    expect(logisticsFired).toBeDefined();
    expect(logisticsFired!.summary).toContain('2');
    expect(logisticsFired!.summary).toContain('120');
  });

  it('bio summary truncates forecast to 80 chars', () => {
    const longForecast = 'A'.repeat(100);
    const payload = makePayload({
      bio: {
        status: 'red',
        burnout_score: 90,
        forecast: longForecast,
        sleep_debt_hours: 5,
        recommendations: [],
      },
    });
    const entry = buildAgentLogEntry(MESSAGE, payload, TIMESTAMP);
    const bioFired = entry.agents_fired.find((a) => a.domain === 'bio');
    expect(bioFired).toBeDefined();
    expect(bioFired!.summary).toContain('A'.repeat(80));
    expect(bioFired!.summary).not.toContain('A'.repeat(81));
  });

  it('carries responding_agent and overall_status from payload', () => {
    const payload = makePayload({
      overall_status: 'red',
      responding_agent: 'bio_archivist',
    });
    const entry = buildAgentLogEntry(MESSAGE, payload, TIMESTAMP);
    expect(entry.responding_agent).toBe('bio_archivist');
    expect(entry.overall_status).toBe('red');
  });
});
