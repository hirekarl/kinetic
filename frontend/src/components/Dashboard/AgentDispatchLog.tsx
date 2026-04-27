import React, { useState } from 'react';
import type { AgentFired, AgentLogEntry } from '../../types';

interface AgentDispatchLogProps {
  entries: AgentLogEntry[];
  isLoading?: boolean;
}

const STATUS_DOT: Record<AgentFired['status'], string> = {
  green: 'bg-status-green',
  yellow: 'bg-status-yellow',
  red: 'bg-status-red',
};

function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max) + '…' : text;
}

export const AgentDispatchLog: React.FC<AgentDispatchLogProps> = ({ entries, isLoading }) => {
  const [panelOpen, setPanelOpen] = useState(false);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleEntry = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div
        className="rounded-2xl border border-zinc-800 bg-zinc-900/30 p-6 animate-pulse"
        aria-label="Loading agent dispatch log"
      >
        <div className="flex items-center justify-between">
          <div className="h-3 w-40 bg-zinc-800 rounded" />
          <div className="h-3 w-6 bg-zinc-800 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/30 transition-all hover:border-zinc-700">
      {/* Panel trigger */}
      <button
        onClick={() => {
          setPanelOpen((prev) => !prev);
        }}
        aria-expanded={panelOpen}
        className="w-full flex items-center justify-between px-6 py-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 rounded-2xl"
      >
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-sky-500 shadow-[0_0_8px_rgba(14,165,233,0.6)]" />
          <span className="text-xs font-bold uppercase tracking-widest text-sky-400">
            Agent Dispatch Log
          </span>
          {entries.length > 0 && (
            <span className="flex items-center justify-center h-4 min-w-4 px-1 rounded-full bg-sky-500/20 text-[10px] font-bold text-sky-300">
              {entries.length}
            </span>
          )}
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`text-zinc-400 transition-transform duration-200 ${panelOpen ? 'rotate-180' : ''}`}
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Collapsible content */}
      {panelOpen && (
        <div className="px-6 pb-6">
          {entries.length === 0 ? (
            <p className="text-sm text-zinc-400 leading-relaxed">No check-ins yet this session.</p>
          ) : (
            <ul className="space-y-2" aria-label="Check-in history">
              {entries.map((entry) => {
                const isExpanded = expandedIds.has(entry.id);
                const time = new Date(entry.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                });
                const truncatedMsg = truncate(entry.user_message, 60);

                return (
                  <li key={entry.id} className="rounded-xl border border-zinc-800 bg-zinc-950/50">
                    {/* Entry trigger */}
                    <button
                      onClick={() => {
                        toggleEntry(entry.id);
                      }}
                      aria-expanded={isExpanded}
                      className="w-full flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 focus-visible:ring-offset-1 focus-visible:ring-offset-zinc-950 rounded-xl"
                    >
                      <span className="text-[10px] font-mono text-zinc-500 shrink-0">{time}</span>
                      <span className="text-xs text-zinc-300 min-w-0">{truncatedMsg}</span>

                      {/* Agent chips */}
                      <span className="flex items-center gap-2 ml-auto">
                        {entry.agents_fired.map((agent) => (
                          <span key={agent.domain} className="flex items-center gap-1">
                            <span
                              aria-hidden="true"
                              className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[agent.status]}`}
                            />
                            <span className="text-[9px] font-bold tracking-wider text-zinc-400">
                              {agent.domain.toUpperCase()}
                            </span>
                          </span>
                        ))}
                      </span>

                      {/* Responding agent badge */}
                      {entry.responding_agent && (
                        <span className="text-[10px] font-mono text-sky-400/70 shrink-0">
                          → {entry.responding_agent}
                        </span>
                      )}
                    </button>

                    {/* Expanded summaries */}
                    {isExpanded && (
                      <ul className="px-4 pb-3 space-y-1 border-t border-zinc-800/50">
                        {entry.agents_fired.map((agent) => (
                          <li key={agent.domain} className="flex items-start gap-2 pt-2">
                            <span
                              className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${STATUS_DOT[agent.status]}`}
                              aria-hidden="true"
                            />
                            <span className="text-xs text-zinc-400">{agent.summary}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
