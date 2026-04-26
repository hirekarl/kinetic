import React, { useState } from 'react';
import { TriageItem } from '../../types';

interface TriageListProps {
  items: TriageItem[];
  isLoading?: boolean;
  onCompleteTask?: (taskName: string) => Promise<void>;
}

export const TriageList: React.FC<TriageListProps> = ({ items, isLoading, onCompleteTask }) => {
  const [optimisticallyRemoved, setOptimisticallyRemoved] = useState<Set<string>>(new Set());

  const handleComplete = async (item: TriageItem) => {
    if (!item.source_id || !onCompleteTask) return;
    const taskName = item.source_id;
    setOptimisticallyRemoved((prev) => new Set(prev).add(item.id));
    try {
      await onCompleteTask(taskName);
    } catch {
      setOptimisticallyRemoved((prev) => {
        const next = new Set(prev);
        next.delete(item.id);
        return next;
      });
    }
  };

  const visibleItems = items.filter((item) => !optimisticallyRemoved.has(item.id));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider">
          Prioritized Triage
        </h2>
        <span className="text-[10px] text-zinc-400">
          {isLoading ? 'Analyzing...' : `${visibleItems.length.toString()} items pending`}
        </span>
      </div>

      {isLoading ? (
        <div className="space-y-2 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-xl border border-zinc-800 bg-zinc-900/50" />
          ))}
        </div>
      ) : visibleItems.length === 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center">
          <p className="text-sm text-zinc-400">All systems nominal. No triage items pending.</p>
        </div>
      ) : (
        <ul className="space-y-2">
          {visibleItems.map((item) => (
            <li
              key={item.id}
              className="flex items-start gap-4 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 transition-colors hover:border-zinc-700"
            >
              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded bg-zinc-800 text-[10px] font-bold text-zinc-400">
                {item.priority}
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-bold uppercase tracking-widest ${
                      item.domain === 'bio'
                        ? 'text-emerald-500'
                        : item.domain === 'logistics'
                          ? 'text-amber-500'
                          : 'text-blue-500'
                    }`}
                  >
                    {item.domain}
                  </span>
                  <p className="text-sm font-medium text-zinc-200">{item.description}</p>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-400">
                  <span className="text-zinc-400 font-bold">NEXT:</span>
                  <span>{item.action}</span>
                </div>
              </div>
              {item.domain === 'logistics' && item.source_id && (
                <button
                  onClick={() => {
                    void handleComplete(item);
                  }}
                  aria-label={`Mark ${item.source_id} complete`}
                  className="shrink-0 flex h-7 w-7 items-center justify-center rounded border border-zinc-700 bg-zinc-800 text-zinc-400 transition-colors hover:border-emerald-600 hover:bg-emerald-950 hover:text-emerald-400"
                >
                  <svg
                    aria-hidden="true"
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
