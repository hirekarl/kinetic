import React from 'react';
import { StatusLevel } from '../../types';

/** Props for the `StatusBadge` component. */
interface StatusBadgeProps {
  /** Operational status level driving the indicator colour. */
  status: StatusLevel;
  /** Optional override for the default label derived from `status`. */
  label?: string;
}

const statusConfig = {
  green: {
    color: 'bg-status-green',
    label: 'Healthy',
    glow: 'shadow-[0_0_8px_rgba(16,185,129,0.4)]',
  },
  yellow: {
    color: 'bg-status-yellow',
    label: 'Degraded',
    glow: 'shadow-[0_0_8px_rgba(245,158,11,0.4)]',
  },
  red: {
    color: 'bg-status-red',
    label: 'Critical',
    glow: 'shadow-[0_0_8px_rgba(244,63,94,0.4)]',
  },
};

/**
 * Small coloured dot + label badge indicating an operational status level.
 *
 * Used in card headers and the top dashboard bar to give at-a-glance system health.
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2">
      <div
        aria-hidden="true"
        className={`h-2 w-2 rounded-full transition-all duration-500 ${config.color} ${config.glow}`}
      />
      <span className="text-xs font-medium text-zinc-400 uppercase tracking-tight">
        {label ?? config.label}
      </span>
    </div>
  );
};
