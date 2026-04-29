import React from 'react';
import { ROISummary } from '../../types';

interface ROISummaryCardProps {
  data: ROISummary;
  isLoading?: boolean;
}

export const ROISummaryCard: React.FC<ROISummaryCardProps> = ({ data, isLoading }) => {
  if (isLoading) {
    // ... skeleton ...
    return (
      <div className="rounded-2xl border border-emerald-500/10 bg-emerald-500/[0.01] p-8 animate-pulse">
        <div className="flex items-center gap-3 mb-6">
          <div className="h-2 w-2 rounded-full bg-emerald-900" />
          <div className="h-2 w-48 bg-emerald-900/50 rounded" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          <div className="space-y-4">
            <div className="h-2 w-20 bg-zinc-800 rounded" />
            <div className="h-8 w-16 bg-zinc-800 rounded" />
          </div>
          <div className="space-y-4 border-l border-zinc-800/50 pl-12">
            <div className="h-2 w-20 bg-zinc-800 rounded" />
            <div className="h-8 w-24 bg-zinc-800 rounded" />
          </div>
          <div className="space-y-4 border-l border-zinc-800/50 pl-12">
            <div className="h-2 w-20 bg-zinc-800 rounded" />
            <div className="h-8 w-24 bg-zinc-800 rounded" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.02] p-8 transition-all hover:border-emerald-500/30">
      <div className="flex items-center gap-3 mb-6">
        <div
          aria-hidden="true"
          className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]"
        />
        <h2 className="text-xs font-bold uppercase tracking-widest text-emerald-500">
          Performance Yield & ROI
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
        {/* Time Recovered */}
        <div className="space-y-1">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
            Time Recovered
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-white">{data.time_recovered_minutes}</span>
            <span className="text-sm font-medium text-zinc-400">min</span>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Potential focus time reclaimed through suggested outsourcing.
          </p>
        </div>

        {/* System Margin */}
        <div className="space-y-1 border-l border-zinc-800/50 pl-12 md:border-l">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
            System Margin
          </div>
          <div className="text-3xl font-bold text-emerald-400">{data.margin_recovered}</div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Aggregate increase in operational capacity and connection margin.
          </p>
        </div>

        {/* Burnout Risk Delta */}
        <div className="space-y-1 border-l border-zinc-800/50 pl-12">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-400">
            Burnout Risk Delta
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white">
              {data.burnout_risk_delta > 0 ? '+' : ''}
              {data.burnout_risk_delta.toFixed(1)}
            </span>
            <span className="text-xs font-bold uppercase text-emerald-500">Projected</span>
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            Forecasted impact on burnout score if recommendations are resolved.
          </p>
        </div>
      </div>
    </div>
  );
};
