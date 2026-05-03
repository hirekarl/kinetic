import React from 'react';

/** Props for the `BurnoutTrendChart` component. */
interface BurnoutTrendChartProps {
  /** Burnout scores (0–100), oldest first. */
  series: number[];
  /** SVG canvas width in pixels. Defaults to `120`. */
  width?: number;
  /** SVG canvas height in pixels. Defaults to `32`. */
  height?: number;
}

function computeSlope(series: number[]): number {
  const n = series.length;
  if (n < 2) return 0;
  const meanX = (n - 1) / 2;
  const meanY = series.reduce((sum, y) => sum + y, 0) / n;
  let num = 0;
  let den = 0;
  for (let i = 0; i < n; i++) {
    num += (i - meanX) * ((series[i] ?? 0) - meanY);
    den += (i - meanX) ** 2;
  }
  return den === 0 ? 0 : num / den;
}

function strokeColor(slope: number): string {
  if (slope > 1.0) return '#ef4444';
  if (slope < -1.0) return '#10b981';
  return '#f59e0b';
}

/**
 * SVG polyline chart for the 14-day burnout score trend.
 *
 * Stroke colour is derived from a linear regression slope: red for worsening,
 * emerald for improving, amber for flat. Returns `null` for fewer than 2 data
 * points. Decorated with a `sr-only` label for screen-reader accessibility.
 */
export const BurnoutTrendChart: React.FC<BurnoutTrendChartProps> = ({
  series,
  width = 120,
  height = 32,
}) => {
  if (series.length < 2) return null;

  const n = series.length;
  const min = Math.min(...series);
  const max = Math.max(...series);
  const range = max - min || 1;

  const x = (i: number) => (i / (n - 1)) * width;
  const y = (v: number) => height - ((v - min) / range) * height;

  const points = series.map((v, i) => `${x(i).toFixed(2)},${y(v).toFixed(2)}`).join(' ');
  const lastX = x(n - 1);
  const lastY = y(series[n - 1] ?? 0);
  const stroke = strokeColor(computeSlope(series));

  return (
    <>
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
      <span className="sr-only">14-day burnout trend</span>
    </>
  );
};
