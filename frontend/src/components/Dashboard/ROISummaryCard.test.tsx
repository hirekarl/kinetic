import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ROISummaryCard } from './ROISummaryCard';
import { ROISummary } from '../../types';

const mockData: ROISummary = {
  time_recovered_minutes: 90,
  margin_recovered: '12% reclaimed',
  burnout_risk_delta: -5.5,
};

describe('ROISummaryCard', () => {
  it('renders the Performance Yield heading', () => {
    render(<ROISummaryCard data={mockData} />);
    expect(screen.getByText(/performance yield/i)).toBeInTheDocument();
  });

  it('renders time recovered value', () => {
    render(<ROISummaryCard data={mockData} />);
    expect(screen.getByText('90')).toBeInTheDocument();
    expect(screen.getByText('min')).toBeInTheDocument();
  });

  it('renders system margin', () => {
    render(<ROISummaryCard data={mockData} />);
    expect(screen.getByText('12% reclaimed')).toBeInTheDocument();
  });

  it('renders negative burnout risk delta', () => {
    render(<ROISummaryCard data={mockData} />);
    expect(screen.getByText('-5.5')).toBeInTheDocument();
  });

  it('renders positive burnout risk delta with + prefix', () => {
    const positiveData: ROISummary = { ...mockData, burnout_risk_delta: 3.2 };
    render(<ROISummaryCard data={positiveData} />);
    expect(screen.getByText('+3.2')).toBeInTheDocument();
  });

  it('renders loading skeleton when isLoading is true', () => {
    render(<ROISummaryCard data={mockData} isLoading={true} />);
    expect(screen.queryByText(/performance yield/i)).not.toBeInTheDocument();
  });

  it('decorative status dot is aria-hidden so screen readers skip it', () => {
    const { container } = render(<ROISummaryCard data={mockData} />);
    const dot = container.querySelector('[aria-hidden="true"]');
    expect(dot).not.toBeNull();
  });
});
