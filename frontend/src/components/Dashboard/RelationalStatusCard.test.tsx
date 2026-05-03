import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { RelationalStatusCard } from './RelationalStatusCard';
import { RelationalStatus } from '../../types';

const mockData: RelationalStatus = {
  status: 'yellow',
  connection_margin_score: 60,
  at_risk_relationships: ['Marcus', 'Jamie'],
  interaction_sprints: ['Send Marcus a check-in today.', 'Call Jamie this week.'],
};

describe('RelationalStatusCard', () => {
  it('renders no-data state when data is null', () => {
    render(<RelationalStatusCard data={null} />);
    expect(screen.getByText('Relational Diplomat')).toBeInTheDocument();
    expect(screen.getByText(/perform vibe checks/i)).toBeInTheDocument();
  });

  it('renders loading skeleton when isLoading is true', () => {
    render(<RelationalStatusCard data={null} isLoading={true} />);
    expect(screen.queryByText('Relational Diplomat')).not.toBeInTheDocument();
  });

  it('renders connection margin score', () => {
    render(<RelationalStatusCard data={mockData} />);
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('renders at-risk relationship badges', () => {
    render(<RelationalStatusCard data={mockData} />);
    expect(screen.getByText('Marcus')).toBeInTheDocument();
    expect(screen.getByText('Jamie')).toBeInTheDocument();
    expect(screen.getByText('Degraded Links')).toBeInTheDocument();
  });

  it('renders interaction sprints', () => {
    render(<RelationalStatusCard data={mockData} />);
    expect(screen.getByText('Send Marcus a check-in today.')).toBeInTheDocument();
    expect(screen.getByText('Call Jamie this week.')).toBeInTheDocument();
  });

  it('renders green nominal message when status is green', () => {
    const greenData: RelationalStatus = {
      ...mockData,
      status: 'green',
      at_risk_relationships: [],
      interaction_sprints: [],
    };
    render(<RelationalStatusCard data={greenData} />);
    expect(screen.getByText(/relationship margins healthy/i)).toBeInTheDocument();
  });

  it('renders error message when provided', () => {
    const withError: RelationalStatus = { ...mockData, error_message: 'Vibe check failed' };
    render(<RelationalStatusCard data={withError} />);
    expect(screen.getByText('Vibe check failed')).toBeInTheDocument();
  });

  it('renders On Break section with person name when activePauses is non-empty', () => {
    const pauses = [{ person: 'Marcus', paused_until: '2026-06-01', reason: 'break' }];
    render(<RelationalStatusCard data={mockData} activePauses={pauses} />);
    expect(screen.getByText('On Break')).toBeInTheDocument();
    expect(screen.getAllByText('Marcus').length).toBeGreaterThan(0);
    expect(screen.getByText(/until/i)).toBeInTheDocument();
  });
});
