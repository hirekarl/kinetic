import type { AgentFired, AgentLogEntry, SystemHealthPayload } from '../types';

/**
 * Derives a structured `AgentLogEntry` from a completed check-in result.
 *
 * Inspects each domain sub-payload (bio, logistics, relational) to build the
 * `agents_fired` list, summarising key metrics per domain so the Agent Dispatch
 * Log can render a compact per-agent breakdown without additional API calls.
 *
 * @param message - The original user message that triggered the check-in.
 * @param payload - The `SystemHealthPayload` returned by the orchestrator.
 * @param timestamp - ISO-8601 timestamp captured at dispatch time.
 * @returns A fully populated `AgentLogEntry` with a stable UUID id.
 */
export function buildAgentLogEntry(
  message: string,
  payload: SystemHealthPayload,
  timestamp: string
): AgentLogEntry {
  const agents_fired: AgentFired[] = [];

  if (payload.bio !== null) {
    agents_fired.push({
      domain: 'bio',
      status: payload.bio.status,
      summary: `Burnout ${String(payload.bio.burnout_score)}/100 · ${payload.bio.forecast.slice(0, 80)}`,
    });
  }

  if (payload.logistics !== null) {
    agents_fired.push({
      domain: 'logistics',
      status: payload.logistics.status,
      summary: `${String(payload.logistics.critical_tasks.length)} critical · ${String(payload.logistics.time_to_resolve_minutes)}min to resolve`,
    });
  }

  if (payload.relational !== null) {
    agents_fired.push({
      domain: 'relational',
      status: payload.relational.status,
      summary: `Connection margin: ${String(payload.relational.connection_margin_score)}/100`,
    });
  }

  return {
    id: crypto.randomUUID(),
    timestamp,
    user_message: message,
    agents_fired,
    responding_agent: payload.responding_agent,
    overall_status: payload.overall_status,
  };
}
