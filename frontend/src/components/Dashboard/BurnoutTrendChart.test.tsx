import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BurnoutTrendChart } from './BurnoutTrendChart';

describe('BurnoutTrendChart', () => {
  it('renders nothing when series is empty', () => {
    const { container } = render(<BurnoutTrendChart series={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when series has exactly 1 point', () => {
    const { container } = render(<BurnoutTrendChart series={[50]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders an SVG when series has 2 or more points', () => {
    const { container } = render(<BurnoutTrendChart series={[40, 60]} />);
    expect(container.querySelector('svg')).not.toBeNull();
  });

  it('SVG has aria-hidden="true"', () => {
    const { container } = render(<BurnoutTrendChart series={[40, 60, 80]} />);
    expect(container.querySelector('svg')).toHaveAttribute('aria-hidden', 'true');
  });

  it('renders a polyline element', () => {
    const { container } = render(<BurnoutTrendChart series={[40, 60, 80]} />);
    expect(container.querySelector('polyline')).not.toBeNull();
  });

  it('renders a terminal dot circle at the last data point', () => {
    const { container } = render(<BurnoutTrendChart series={[40, 60, 80]} />);
    expect(container.querySelector('circle')).not.toBeNull();
  });

  it('renders sr-only text for screen readers', () => {
    render(<BurnoutTrendChart series={[40, 60, 80]} />);
    expect(screen.getByText(/14-day burnout trend/i)).toBeInTheDocument();
  });

  it('uses red stroke when burnout is worsening (slope > 1.0)', () => {
    // [30, 80]: slope = 50 >> 1.0 → red
    const { container } = render(<BurnoutTrendChart series={[30, 80]} />);
    expect(container.querySelector('polyline')).toHaveAttribute('stroke', '#ef4444');
  });

  it('uses emerald stroke when burnout is improving (slope < -1.0)', () => {
    // [80, 30]: slope = -50 << -1.0 → emerald
    const { container } = render(<BurnoutTrendChart series={[80, 30]} />);
    expect(container.querySelector('polyline')).toHaveAttribute('stroke', '#10b981');
  });

  it('uses amber stroke when burnout is flat (slope between -1.0 and +1.0)', () => {
    // [60, 60]: slope = 0 → amber
    const { container } = render(<BurnoutTrendChart series={[60, 60]} />);
    expect(container.querySelector('polyline')).toHaveAttribute('stroke', '#f59e0b');
  });

  it('uses amber stroke when slope is exactly at boundary (slope = 1.0 is not worsening)', () => {
    // [49, 50]: slope = 1.0 → NOT > 1.0 → amber
    const { container } = render(<BurnoutTrendChart series={[49, 50]} />);
    expect(container.querySelector('polyline')).toHaveAttribute('stroke', '#f59e0b');
  });

  it('uses amber stroke when slope is exactly -1.0 (boundary, not improving)', () => {
    // [50, 49]: slope = -1.0 → NOT < -1.0 → amber
    const { container } = render(<BurnoutTrendChart series={[50, 49]} />);
    expect(container.querySelector('polyline')).toHaveAttribute('stroke', '#f59e0b');
  });

  it('handles a flat series without NaN in point coordinates', () => {
    const { container } = render(<BurnoutTrendChart series={[60, 60, 60]} />);
    const polyline = container.querySelector('polyline');
    expect(polyline).not.toBeNull();
    const points = polyline?.getAttribute('points') ?? '';
    points.split(' ').forEach((pair) => {
      const [x, y] = pair.split(',').map(Number);
      expect(Number.isFinite(x)).toBe(true);
      expect(Number.isFinite(y)).toBe(true);
    });
  });

  it('renders exactly 2 point pairs with a 2-element series', () => {
    const { container } = render(<BurnoutTrendChart series={[40, 80]} />);
    const polyline = container.querySelector('polyline');
    const pairs = (polyline?.getAttribute('points') ?? '').trim().split(' ');
    expect(pairs).toHaveLength(2);
  });

  it('accepts custom width and height props', () => {
    const { container } = render(<BurnoutTrendChart series={[40, 60]} width={200} height={48} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '200');
    expect(svg).toHaveAttribute('height', '48');
  });

  it('circle fill matches polyline stroke color', () => {
    const { container } = render(<BurnoutTrendChart series={[30, 90]} />);
    const polyline = container.querySelector('polyline');
    const circle = container.querySelector('circle');
    expect(circle).toHaveAttribute('fill', polyline?.getAttribute('stroke'));
  });

  it('uses 0 fallback when last series element is undefined (nullish guard at chart level)', () => {
    const seriesWithHole = [40, 60, undefined as unknown as number];
    const { container } = render(<BurnoutTrendChart series={seriesWithHole} />);
    expect(container.querySelector('circle')).not.toBeNull();
  });

  it('uses 0 fallback in slope loop when series element is undefined', () => {
    const seriesWithHole = [40, undefined as unknown as number, 60];
    const { container } = render(<BurnoutTrendChart series={seriesWithHole} />);
    expect(container.querySelector('polyline')).not.toBeNull();
  });
});
