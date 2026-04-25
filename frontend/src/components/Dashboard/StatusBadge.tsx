import React from 'react';
import { StatusLevel } from '../../types';

interface StatusBadgeProps {
  status: StatusLevel;
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

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const config = statusConfig[status];

  return (
    <div className="flex items-center gap-2">
      <div className={`h-2 w-2 rounded-full ${config.color} ${config.glow}`} />
      <span className="text-xs font-medium text-zinc-400 uppercase tracking-tight">
        {label ?? config.label}
      </span>
    </div>
  );
};
