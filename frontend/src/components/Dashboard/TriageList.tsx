import React from 'react';
import { TriageItem } from '../../types';

interface TriageListProps {
  items: TriageItem[];
  isLoading?: boolean;
}

export const TriageList: React.FC<TriageListProps> = ({ items, isLoading }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider">
          Prioritized Triage
        </h2>
        <span className="text-[10px] text-zinc-400">
          {isLoading ? 'Analyzing...' : `${items.length.toString()} items pending`}
        </span>
      </div>

      {isLoading ? (
        <div className="space-y-2 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-xl border border-zinc-800 bg-zinc-900/50" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center">
          <p className="text-sm text-zinc-400">All systems nominal. No triage items pending.</p>
        </div>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
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
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
