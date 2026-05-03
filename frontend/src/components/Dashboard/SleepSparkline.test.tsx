import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { SleepSparkline } from './SleepSparkline';

describe('SleepSparkline', () => {
  it('renders nothing when series is empty', () => {
    const { container } = render(<SleepSparkline series={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when series has exactly 1 point', () => {
    const { container } = render(<SleepSparkline series={[7.0]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders an SVG when series has 2 or more points', () => {
    const { container } = render(<SleepSparkline series={[7.0, 6.5, 6.0]} />);
    expect(container.querySelector('svg')).not.toBeNull();
  });

  it('SVG has aria-hidden="true"', () => {
    const { container } = render(<SleepSparkline series={[7.0, 6.5, 6.0]} />);
    expect(container.querySelector('svg')).toHaveAttribute('aria-hidden', 'true');
  });

  it('renders a polyline element', () => {
    const { container } = render(<SleepSparkline series={[7.0, 6.5, 6.0]} />);
    expect(container.querySelector('polyline')).not.toBeNull();
  });

  it('uses amber stroke when declining=true', () => {
    const { container } = render(<SleepSparkline series={[7.5, 6.5, 5.5]} declining={true} />);
    expect(container.querySelector('polyline')).toHaveAttribute('stroke', '#f59e0b');
  });

  it('uses emerald stroke when declining=false', () => {
    const { container } = render(<SleepSparkline series={[5.5, 6.5, 7.5]} declining={false} />);
    expect(container.querySelector('polyline')).toHaveAttribute('stroke', '#10b981');
  });

  it('defaults to emerald stroke when declining is omitted', () => {
    const { container } = render(<SleepSparkline series={[6.0, 6.5, 7.0]} />);
    expect(container.querySelector('polyline')).toHaveAttribute('stroke', '#10b981');
  });

  it('renders a terminal dot circle at the last data point', () => {
    const { container } = render(<SleepSparkline series={[7.0, 6.5, 6.0]} />);
    expect(container.querySelector('circle')).not.toBeNull();
  });

  it('handles a flat series without NaN in point coordinates', () => {
    const { container } = render(<SleepSparkline series={[7.0, 7.0, 7.0]} />);
    const polyline = container.querySelector('polyline');
    expect(polyline).not.toBeNull();
    const points = polyline?.getAttribute('points') ?? '';
    points.split(' ').forEach((pair) => {
      const [x, y] = pair.split(',').map(Number);
      expect(Number.isFinite(x)).toBe(true);
      expect(Number.isFinite(y)).toBe(true);
    });
  });

  it('uses 0 as fallback when last series element is undefined (nullish guard)', () => {
    const seriesWithHole = [7.0, 6.5, undefined as unknown as number];
    const { container } = render(<SleepSparkline series={seriesWithHole} />);
    expect(container.querySelector('circle')).not.toBeNull();
  });

  it('renders exactly 2 points with a 2-element series', () => {
    const { container } = render(<SleepSparkline series={[8.0, 6.0]} />);
    const polyline = container.querySelector('polyline');
    const pairs = (polyline?.getAttribute('points') ?? '').trim().split(' ');
    expect(pairs).toHaveLength(2);
  });
});
