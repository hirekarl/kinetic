import React from 'react';

/** Animated placeholder card rendered while a status card's data is loading. */
export const CardSkeleton: React.FC = () => {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 animate-pulse">
      <div className="flex items-center justify-between mb-6">
        <div className="h-4 w-32 bg-zinc-800 rounded" />
        <div className="h-2 w-12 bg-zinc-800 rounded-full" />
      </div>

      <div className="mb-6 grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="h-2 w-16 bg-zinc-800 rounded" />
          <div className="h-8 w-12 bg-zinc-800 rounded" />
        </div>
        <div className="space-y-2">
          <div className="h-2 w-16 bg-zinc-800 rounded" />
          <div className="h-8 w-12 bg-zinc-800 rounded" />
        </div>
      </div>

      <div className="space-y-3">
        <div className="h-16 w-full bg-zinc-800/50 rounded-lg" />
        <div className="h-4 w-3/4 bg-zinc-800/50 rounded" />
        <div className="h-4 w-1/2 bg-zinc-800/50 rounded" />
      </div>
    </div>
  );
};
