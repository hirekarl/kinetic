import React from 'react';

/** Props for the `SleepSparkline` component. */
interface SleepSparklineProps {
  /** Per-day sleep hours, oldest first. */
  series: number[];
  /** SVG canvas width in pixels. Defaults to `120`. */
  width?: number;
  /** SVG canvas height in pixels. Defaults to `32`. */
  height?: number;
  /** When `true`, uses amber stroke to signal a declining trend; otherwise emerald. */
  declining?: boolean;
}

/**
 * Pure SVG polyline sparkline for the 7-day sleep trend.
 *
 * Returns `null` when fewer than 2 data points are provided — a single point
 * cannot form a meaningful trend line.
 */
export const SleepSparkline: React.FC<SleepSparklineProps> = ({
  series,
  width = 120,
  height = 32,
  declining = false,
}) => {
  if (series.length < 2) return null;

  const n = series.length;
  const min = Math.min(...series);
  const max = Math.max(...series);
  const range = max - min || 1; // guard flat series

  const x = (i: number) => (i / (n - 1)) * width;
  const y = (v: number) => height - ((v - min) / range) * height;

  const points = series.map((v, i) => `${x(i).toFixed(2)},${y(v).toFixed(2)}`).join(' ');

  const lastX = x(n - 1);
  const lastY = y(series[n - 1] ?? 0);
  const stroke = declining ? '#f59e0b' : '#10b981';

  return (
    <svg
      aria-hidden="true"
      width={width}
      height={height}
      viewBox={[0, 0, width, height].join(' ')}
      overflow="visible"
    >
      <polyline
        points={points}
        fill="none"
        stroke={stroke}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={lastX} cy={lastY} r={2} fill={stroke} />
    </svg>
  );
};
