import React from 'react';
import { RelationalStatus } from '../../types';
import { StatusBadge } from './StatusBadge';

interface RelationalStatusCardProps {
  data: RelationalStatus | null;
}

export const RelationalStatusCard: React.FC<RelationalStatusCardProps> = ({ data }) => {
  if (!data) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 opacity-50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-zinc-400">Relational Diplomat</h3>
          <span className="text-[10px] uppercase text-zinc-600">No Data</span>
        </div>
        <div className="text-sm text-zinc-500">Perform vibe checks on key relationships.</div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 transition-colors hover:border-zinc-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-zinc-100">Relational Diplomat</h3>
        <StatusBadge status={data.status} />
      </div>

      <div className="mb-6">
        <div className="text-[10px] uppercase tracking-wider text-zinc-500 mb-1">
          Connection Margin
        </div>
        <div className="text-2xl font-bold text-zinc-100">
          {data.connection_margin_score.toFixed(0)}%
        </div>
      </div>

      {data.at_risk_relationships.length > 0 && (
        <div className="mb-6">
          <div className="text-[10px] uppercase tracking-wider text-zinc-500 mb-2">
            Degraded Links
          </div>
          <div className="flex flex-wrap gap-2">
            {data.at_risk_relationships.map((person) => (
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

      {data.interaction_sprints.length > 0 && (
        <div className="space-y-3">
          <div className="text-[10px] uppercase tracking-wider text-zinc-500 font-semibold">
            Interaction Sprints
          </div>
          {data.interaction_sprints.map((sprint, i) => (
            <div
              key={i}
              className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-sm text-zinc-400 flex items-start gap-3"
            >
              <span className="text-zinc-600 font-mono text-xs mt-0.5">[{i + 1}]</span>
              <p className="leading-relaxed">{sprint}</p>
            </div>
          ))}
        </div>
      )}

      {data.status === 'green' && (
        <p className="text-sm text-zinc-500 italic">
          Relationship margins healthy. Connections maintained.
        </p>
      )}
    </div>
  );
};
