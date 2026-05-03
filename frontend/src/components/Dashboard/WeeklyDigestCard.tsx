import React, { useState } from 'react';
import type { DigestResponse } from '../../types';

/** Props for the `WeeklyDigestCard` component. */
interface WeeklyDigestCardProps {
  /** Digest data from the server, or `null` when not yet loaded. */
  digest: DigestResponse | null;
  /** When `true`, renders a `role="status"` skeleton in place of the card. */
  isLoading?: boolean;
  /** Optional callback to trigger a force-refresh of the digest. */
  onRefresh?: () => void | Promise<void>;
  /** When `true`, the Refresh button shows a spinner. */
  isRefreshing?: boolean;
}

function relativeTime(isoString: string): string {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${String(diffMins)} minute${diffMins === 1 ? '' : 's'} ago`;
  const diffHours = Math.floor(diffMins / 60);
  return `${String(diffHours)} hour${diffHours === 1 ? '' : 's'} ago`;
}

const NO_DATA_MESSAGE = 'No check-in data yet. Start briefing Kinetic to build your weekly digest.';

/**
 * Collapsible "Weekly Review" card displaying the AI-generated digest summary.
 *
 * Handles three content states: no data yet, a `[DIGEST ERROR]` prefix in the
 * summary string (rendered as an error block), and the normal prose summary.
 * A relative timestamp ("Generated X minutes ago") is shown below the summary.
 */
export const WeeklyDigestCard: React.FC<WeeklyDigestCardProps> = ({
  digest,
  isLoading,
  onRefresh,
  isRefreshing,
}) => {
  const [open, setOpen] = useState(false);

  if (isLoading) {
    return (
      <div
        role="status"
        className="rounded-2xl border border-zinc-800 bg-zinc-900/30 p-6 animate-pulse"
        aria-label="Loading weekly digest"
      >
        <div className="flex items-center justify-between">
          <div className="h-3 w-40 bg-zinc-800 rounded" />
          <div className="h-3 w-6 bg-zinc-800 rounded" />
        </div>
      </div>
    );
  }

  const isError = Boolean(digest?.summary.startsWith('[DIGEST ERROR]'));
  const errorText = digest && isError ? digest.summary.slice('[DIGEST ERROR] '.length) : null;

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/30 transition-all hover:border-zinc-700">
      <button
        onClick={() => {
          setOpen((prev) => !prev);
        }}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-6 py-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950 rounded-2xl"
      >
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]" />
          <span className="text-xs font-bold uppercase tracking-widest text-emerald-400">
            Weekly Review
          </span>
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
          className={`text-zinc-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="px-6 pb-6">
          {!digest ? (
            <p className="text-sm text-zinc-400 leading-relaxed">{NO_DATA_MESSAGE}</p>
          ) : isError ? (
            <div className="rounded border border-status-red/20 bg-status-red/5 p-3 text-xs text-status-red">
              <span className="font-bold">DIGEST ERROR:</span> {errorText}
            </div>
          ) : (
            <p className="text-sm text-zinc-300 leading-relaxed">{digest.summary}</p>
          )}

          {digest && (
            <p className="mt-3 text-[10px] text-zinc-400">
              Generated {relativeTime(digest.generated_at)}
            </p>
          )}

          {onRefresh && (
            <button
              onClick={() => {
                void onRefresh();
              }}
              disabled={isRefreshing}
              aria-label={isRefreshing ? 'Refreshing' : 'Refresh'}
              className="mt-4 flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:text-zinc-200 transition-colors disabled:opacity-50"
            >
              {isRefreshing ? (
                <>
                  <svg
                    className="animate-spin h-3 w-3"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Refreshing
                </>
              ) : (
                'Refresh'
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );
};
