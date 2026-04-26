import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { LogisticsStatusCard } from './LogisticsStatusCard';
import { LogisticsStatus } from '../../types';

const mockData: LogisticsStatus = {
  status: 'yellow',
  critical_tasks: ['laundry', 'grocery run'],
  tasks_with_steps: [
    {
      name: 'laundry',
      status: 'pending',
      days_overdue: 3,
      priority: 'high',
      subtasks: ['Sort clothes', 'Run wash', 'Fold'],
      completed_subtasks: ['Sort clothes'],
      notes: null,
    },
  ],
  outsourcing_suggestions: ['Hire TaskRabbit for grocery run.'],
  time_to_resolve_minutes: 90,
};

describe('LogisticsStatusCard', () => {
  it('renders no-data state when data is null', () => {
    render(<LogisticsStatusCard data={null} />);
    expect(screen.getByText('Logistics Fixer')).toBeInTheDocument();
    expect(screen.getByText(/mention domestic tasks/i)).toBeInTheDocument();
  });

  it('renders loading skeleton when isLoading is true', () => {
    render(<LogisticsStatusCard data={null} isLoading={true} />);
    expect(screen.queryByText('Logistics Fixer')).not.toBeInTheDocument();
  });

  it('renders critical task count and resolve time', () => {
    render(<LogisticsStatusCard data={mockData} />);
    // 2 critical tasks
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('90m')).toBeInTheDocument();
  });

  it('renders active blocker badges for critical tasks', () => {
    render(<LogisticsStatusCard data={mockData} />);
    // "laundry" appears in both the blocker badge and the task progress section
    expect(screen.getAllByText('laundry').length).toBeGreaterThan(0);
    expect(screen.getByText('grocery run')).toBeInTheDocument();
  });

  it('renders task progress section', () => {
    render(<LogisticsStatusCard data={mockData} />);
    expect(screen.getByText('Task Progress')).toBeInTheDocument();
    expect(screen.getByText('1/3 steps')).toBeInTheDocument();
  });

  it('renders outsourcing ROI suggestions', () => {
    render(<LogisticsStatusCard data={mockData} />);
    expect(screen.getByText('Hire TaskRabbit for grocery run.')).toBeInTheDocument();
    expect(screen.getByText('Outsourcing ROI')).toBeInTheDocument();
  });

  it('renders green nominal message when status is green', () => {
    const greenData: LogisticsStatus = {
      ...mockData,
      status: 'green',
      critical_tasks: [],
      tasks_with_steps: [],
      outsourcing_suggestions: [],
    };
    render(<LogisticsStatusCard data={greenData} />);
    expect(screen.getByText(/all logistical systems nominal/i)).toBeInTheDocument();
  });

  it('renders error message when provided', () => {
    const withError: LogisticsStatus = { ...mockData, error_message: 'Parser failed' };
    render(<LogisticsStatusCard data={withError} />);
    expect(screen.getByText('Parser failed')).toBeInTheDocument();
  });

  it('task progress bar has progressbar role with ARIA value attributes', () => {
    render(<LogisticsStatusCard data={mockData} />);
    const progressbar = screen.getByRole('progressbar', { name: /laundry progress/i });
    expect(progressbar).toBeInTheDocument();
    // 1 of 3 subtasks complete → Math.round(1/3 * 100) = 33
    expect(progressbar).toHaveAttribute('aria-valuenow', '33');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });
});
