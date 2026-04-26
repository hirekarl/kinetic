import React from 'react';
import { BioStatus } from '../../types';
import { StatusBadge } from './StatusBadge';
import { CardSkeleton } from './CardSkeleton';

interface BioStatusCardProps {
  data: BioStatus | null;
  isLoading?: boolean;
}

export const BioStatusCard: React.FC<BioStatusCardProps> = ({ data, isLoading }) => {
  if (isLoading) return <CardSkeleton />;

  if (!data) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 opacity-50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-zinc-400">Bio-Metric Archivist</h3>
          <span className="text-[10px] uppercase text-zinc-400">No Data</span>
        </div>
        <div className="text-sm text-zinc-400">Brief Kinetic on your sleep or energy levels.</div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 transition-colors hover:border-zinc-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-zinc-100">Bio-Metric Archivist</h3>
        <StatusBadge status={data.status} />
      </div>

      {data.error_message && (
        <div className="mb-6 rounded border border-status-red/20 bg-status-red/5 p-3 text-xs text-status-red">
          <span className="font-bold">AGENT ERROR:</span> {data.error_message}
        </div>
      )}

      <div className="mb-6 grid grid-cols-2 gap-4">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-zinc-400 mb-1">
            Burnout Score
          </div>
          <div className="text-2xl font-bold text-zinc-100">{data.burnout_score.toFixed(0)}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-zinc-400 mb-1">Sleep Debt</div>
          <div className="text-2xl font-bold text-zinc-100">{data.sleep_debt_hours}h</div>
        </div>
      </div>

      <div className="mb-6 p-3 rounded-lg bg-zinc-950/50 border border-zinc-800/50">
        <div className="text-[10px] uppercase tracking-wider text-zinc-400 mb-2">Forecast</div>
        <p className="text-sm text-zinc-300 leading-relaxed">{data.forecast}</p>
      </div>

      {data.recommendations.length > 0 && (
        <div>
          <div className="text-[10px] uppercase tracking-wider text-zinc-400 mb-3">
            Recommendations
          </div>
          <ul className="space-y-2">
            {data.recommendations.map((rec, i) => (
              <li key={i} className="flex gap-2 text-sm text-zinc-400">
                <span className="text-zinc-400">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
