import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BioStatusCard } from './BioStatusCard';
import { BehavioralSummary, BioStatus } from '../../types';

const mockBehavioralSummary: BehavioralSummary = {
  bio_trend: {
    avg_sleep_hours: 6.5,
    sleep_slope: -0.25,
    avg_nutrition: 7.0,
    avg_energy: 6.0,
    worst_sleep_day: null,
    days_analyzed: 3,
    sleep_series: [7.0, 6.5, 6.0],
  },
  recurring_tasks: [],
  relational_drifts: [],
  days_analyzed: 3,
  generated_at: '2026-04-26T10:00:00',
};

const mockData: BioStatus = {
  status: 'yellow',
  burnout_score: 65,
  forecast: 'Moderate burnout risk over 48 hours.',
  sleep_debt_hours: 2.5,
  recommendations: ['Hard stop at 11pm', 'No caffeine after 2pm'],
};

describe('BioStatusCard', () => {
  it('renders no-data state when data is null', () => {
    render(<BioStatusCard data={null} />);
    expect(screen.getByText('Bio-Metric Archivist')).toBeInTheDocument();
    expect(screen.getByText(/brief kinetic on your sleep/i)).toBeInTheDocument();
  });

  it('renders loading skeleton when isLoading is true', () => {
    render(<BioStatusCard data={null} isLoading={true} />);
    expect(screen.queryByText('Bio-Metric Archivist')).not.toBeInTheDocument();
  });

  it('renders burnout score and sleep debt with data', () => {
    render(<BioStatusCard data={mockData} />);
    expect(screen.getByText('65')).toBeInTheDocument();
    expect(screen.getByText('2.5h')).toBeInTheDocument();
    expect(screen.getByText('Moderate burnout risk over 48 hours.')).toBeInTheDocument();
  });

  it('renders all recommendations', () => {
    render(<BioStatusCard data={mockData} />);
    expect(screen.getByText('Hard stop at 11pm')).toBeInTheDocument();
    expect(screen.getByText('No caffeine after 2pm')).toBeInTheDocument();
  });

  it('renders error message when provided', () => {
    const withError: BioStatus = { ...mockData, error_message: 'Gemini API timeout' };
    render(<BioStatusCard data={withError} />);
    expect(screen.getByText('Gemini API timeout')).toBeInTheDocument();
    expect(screen.getByText('AGENT ERROR:')).toBeInTheDocument();
  });

  it('renders without recommendations section when list is empty', () => {
    const noRecs: BioStatus = { ...mockData, recommendations: [] };
    render(<BioStatusCard data={noRecs} />);
    expect(screen.queryByText(/recommendations/i)).not.toBeInTheDocument();
  });

  it('renders sparkline and label when behavioralSummary has sleep_series ≥ 2', () => {
    render(<BioStatusCard data={mockData} behavioralSummary={mockBehavioralSummary} />);
    expect(screen.getByText(/7-day sleep trend/i)).toBeInTheDocument();
  });

  it('does not render sparkline when behavioralSummary is null', () => {
    render(<BioStatusCard data={mockData} behavioralSummary={null} />);
    expect(screen.queryByText(/7-day sleep trend/i)).not.toBeInTheDocument();
  });

  it('does not render sparkline when behavioralSummary is omitted', () => {
    render(<BioStatusCard data={mockData} />);
    expect(screen.queryByText(/7-day sleep trend/i)).not.toBeInTheDocument();
  });

  it('does not render sparkline when sleep_series has fewer than 2 entries', () => {
    const thinSummary: BehavioralSummary = {
      ...mockBehavioralSummary,
      bio_trend: { ...mockBehavioralSummary.bio_trend!, sleep_series: [7.0] },
    };
    render(<BioStatusCard data={mockData} behavioralSummary={thinSummary} />);
    expect(screen.queryByText(/7-day sleep trend/i)).not.toBeInTheDocument();
  });
});
