import React from 'react';
import { LogisticsStatus } from '../../types';
import { StatusBadge } from './StatusBadge';
import { CardSkeleton } from './CardSkeleton';

interface LogisticsStatusCardProps {
  data: LogisticsStatus | null;
  isLoading?: boolean;
}

export const LogisticsStatusCard: React.FC<LogisticsStatusCardProps> = ({ data, isLoading }) => {
  if (isLoading) return <CardSkeleton />;

  if (!data) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 opacity-50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-zinc-400">Logistics Fixer</h3>
          <span className="text-[10px] uppercase text-zinc-400">No Data</span>
        </div>
        <div className="text-sm text-zinc-400">Mention domestic tasks or chores to triage.</div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 transition-colors hover:border-zinc-700">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-zinc-100">Logistics Fixer</h3>
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
            Critical Tasks
          </div>
          <div className="text-2xl font-bold text-zinc-100">{data.critical_tasks.length}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-zinc-400 mb-1">
            Resolve Time
          </div>
          <div className="text-2xl font-bold text-zinc-100">{data.time_to_resolve_minutes}m</div>
        </div>
      </div>

      {data.tasks_with_steps.length > 0 && (
        <div className="mb-6 space-y-4">
          <div className="text-[10px] uppercase tracking-wider text-zinc-400 mb-2">
            Task Progress
          </div>
          {data.tasks_with_steps.map((task) => (
            <div key={task.name} className="space-y-1">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-zinc-200">{task.name}</span>
                <span className="text-zinc-400">
                  {task.completed_subtasks.length.toString()}/{task.subtasks.length.toString()}{' '}
                  steps
                </span>
              </div>
              <div
                role="progressbar"
                aria-label={`${task.name} progress`}
                aria-valuenow={
                  task.subtasks.length > 0
                    ? Math.round((task.completed_subtasks.length / task.subtasks.length) * 100)
                    : 0
                }
                aria-valuemin={0}
                aria-valuemax={100}
                className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden"
              >
                <div
                  className={`h-full transition-all duration-500 ${
                    task.status === 'completed' ? 'bg-status-green' : 'bg-status-yellow'
                  }`}
                  style={{
                    width: `${(task.subtasks.length > 0 ? (task.completed_subtasks.length / task.subtasks.length) * 100 : 0).toString()}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {data.critical_tasks.length > 0 && (
        <div className="mb-6">
          <div className="text-[10px] uppercase tracking-wider text-zinc-400 mb-2 text-status-red">
            Active Blockers
          </div>
          <div className="flex flex-wrap gap-2">
            {data.critical_tasks.map((task) => (
              <span
                key={task}
                className="rounded border border-status-red/30 bg-status-red/5 px-2 py-0.5 text-[10px] font-medium text-status-red uppercase tracking-tight"
              >
                {task}
              </span>
            ))}
          </div>
        </div>
      )}

      {data.outsourcing_suggestions.length > 0 && (
        <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 p-4">
          <div className="text-[10px] uppercase tracking-wider text-emerald-500 mb-2 font-semibold">
            Outsourcing ROI
          </div>
          <ul className="space-y-3">
            {data.outsourcing_suggestions.map((suggestion, i) => (
              <li key={i} className="text-sm text-zinc-300 leading-snug">
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.status === 'green' && (
        <p className="text-sm text-zinc-400 italic">
          All logistical systems nominal. No critical tasks pending.
        </p>
      )}
    </div>
  );
};
