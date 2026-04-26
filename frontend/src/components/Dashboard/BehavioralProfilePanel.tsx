import React, { useState } from 'react';
import { BehavioralProfile } from '../../types';

interface BehavioralProfilePanelProps {
  profiles: BehavioralProfile[];
  isLoading?: boolean;
}

export const BehavioralProfilePanel: React.FC<BehavioralProfilePanelProps> = ({
  profiles,
  isLoading,
}) => {
  const [open, setOpen] = useState(false);

  if (isLoading) {
    return (
      <div
        className="rounded-2xl border border-zinc-800 bg-zinc-900/30 p-6 animate-pulse"
        aria-label="Loading behavioral profile"
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
      {/* Trigger */}
      <button
        onClick={() => {
          setOpen((prev) => !prev);
        }}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-6 py-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 rounded-2xl"
      >
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-violet-500 shadow-[0_0_8px_rgba(139,92,246,0.6)]" />
          <span className="text-xs font-bold uppercase tracking-widest text-violet-400">
            Behavioral Profile
          </span>
          {profiles.length > 0 && (
            <span className="flex items-center justify-center h-4 min-w-4 px-1 rounded-full bg-violet-500/20 text-[10px] font-bold text-violet-300">
              {profiles.length}
            </span>
          )}
        </div>
        {/* Chevron */}
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
          className={`text-zinc-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Collapsible content */}
      {open && (
        <div>
          <div className="px-6 pb-6">
            {profiles.length === 0 ? (
              <p className="text-sm text-zinc-400 leading-relaxed">
                Building your profile — check in again tomorrow.
              </p>
            ) : (
              <ul className="space-y-4" aria-label="Behavioral patterns">
                {profiles.map((profile) => (
                  <li
                    key={profile.profile_key}
                    className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4"
                  >
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <span className="text-[10px] font-mono font-semibold text-violet-300 bg-violet-500/10 px-2 py-0.5 rounded">
                        {profile.profile_key}
                      </span>
                      <span className="shrink-0 text-[10px] font-semibold text-zinc-400">
                        {profile.observation_count} observations
                      </span>
                    </div>
                    <p className="text-sm text-zinc-300 leading-relaxed">{profile.insight}</p>
                    <p className="mt-2 text-[10px] text-zinc-400">
                      Last updated:{' '}
                      {new Date(profile.last_updated).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
