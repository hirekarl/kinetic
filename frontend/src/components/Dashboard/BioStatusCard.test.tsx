import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BioStatusCard } from './BioStatusCard';
import { BioStatus } from '../../types';

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
});
