import React from 'react';
import { ContactPause, RelationalStatus } from '../../types';
import { StatusBadge } from './StatusBadge';
import { CardSkeleton } from './CardSkeleton';

/** Props for the `RelationalStatusCard` component. */
interface RelationalStatusCardProps {
  /** Relational agent output, or `null` when the agent has not run yet. */
  data: RelationalStatus | null;
  /** When `true`, renders a `CardSkeleton` placeholder. */
  isLoading?: boolean;
  /** Active contact pauses from `SystemHealthPayload`; displayed in the "On Break" section. */
  activePauses?: ContactPause[];
}

/**
 * Dashboard card displaying relational agent output: connection margin score,
 * degraded relationship links, interaction sprints, and active contact pauses.
 *
 * Renders a dimmed empty state when `data` is `null`, and a `CardSkeleton`
 * when `isLoading` is `true`.
 */
export const RelationalStatusCard: React.FC<RelationalStatusCardProps> = ({
  data,
  isLoading,
  activePauses = [],
}) => {
  if (isLoading) return <CardSkeleton />;

  if (!data) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 opacity-50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-zinc-400">Relational Diplomat</h3>
          <span className="text-[10px] uppercase text-zinc-400">No Data</span>
        </div>
        <div className="text-sm text-zinc-400">Perform vibe checks on key relationships.</div>
      </div>
    );
  }

  const atRisk = data.at_risk_relationships;
  const sprints = data.interaction_sprints;

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 transition-colors hover:border-zinc-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-zinc-100">Relational Diplomat</h3>
        <StatusBadge status={data.status} />
      </div>

      {data.error_message && (
        <div className="mb-6 rounded border border-status-red/20 bg-status-red/5 p-3 text-xs text-status-red">
          <span className="font-bold">AGENT ERROR:</span> {data.error_message}
        </div>
      )}

      <div className="mb-6">
        <div className="text-[10px] uppercase tracking-wider text-zinc-400 mb-1">
          Connection Margin
        </div>
        <div className="text-2xl font-bold text-zinc-100">
          {data.connection_margin_score.toFixed(0)}%
        </div>
      </div>

      {atRisk.length > 0 && (
        <div className="mb-6">
          <div className="text-[10px] uppercase tracking-wider text-zinc-400 mb-2">
            Degraded Links
          </div>
          <div className="flex flex-wrap gap-2">
            {atRisk.map((person) => (
              <span
                key={person}
                className="rounded border border-zinc-700 bg-zinc-800 px-2 py-0.5 text-[10px] font-medium text-zinc-300 uppercase tracking-tight"
              >
                {person}
              </span>
            ))}
          </div>
        </div>
      )}

      {sprints.length > 0 && (
        <div className="space-y-3">
          <div className="text-[10px] uppercase tracking-wider text-zinc-400 font-semibold">
            Interaction Sprints
          </div>
          {sprints.map((sprint, i) => (
            <div
              key={i}
              className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-sm text-zinc-400 flex items-start gap-3"
            >
              <span className="text-zinc-400 font-mono text-xs mt-0.5">[{i + 1}]</span>
              <p className="leading-relaxed">{sprint}</p>
            </div>
          ))}
        </div>
      )}

      {activePauses.length > 0 && (
        <div className="mt-6">
          <div className="text-[10px] uppercase tracking-wider text-zinc-400 mb-2">On Break</div>
          <div className="space-y-2">
            {activePauses.map((pause) => (
              <div
                key={pause.person}
                className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2"
              >
                <span className="text-sm font-medium text-zinc-300">{pause.person}</span>
                <span className="text-[10px] font-mono text-zinc-500">
                  until{' '}
                  {new Date(pause.paused_until).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.status === 'green' && activePauses.length === 0 && (
        <p className="text-sm text-zinc-400 italic">
          Relationship margins healthy. Connections maintained.
        </p>
      )}
    </div>
  );
};
