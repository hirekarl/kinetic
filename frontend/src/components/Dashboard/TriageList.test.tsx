import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TriageList } from './TriageList';
import { TriageItem } from '../../types';

const mockItems: TriageItem[] = [
  {
    id: 'bio-001',
    priority: 9,
    domain: 'bio',
    description: 'Sleep debt critical',
    action: 'Hard stop at 10pm',
    snooze_until: null,
    completed: false,
    source_id: null,
  },
  {
    id: 'logistics-001',
    priority: 6,
    domain: 'logistics',
    description: 'Laundry overdue',
    action: 'Run a load tonight',
    snooze_until: null,
    completed: false,
    source_id: 'laundry',
  },
  {
    id: 'relational-001',
    priority: 6,
    domain: 'relational',
    description: 'Marcus: contact drift',
    action: 'Send a message',
    snooze_until: null,
    completed: false,
    source_id: null,
  },
];

describe('TriageList', () => {
  it('renders the "Prioritized Triage" heading', () => {
    render(<TriageList items={[]} />);
    expect(screen.getByText('Prioritized Triage')).toBeInTheDocument();
  });

  it('renders empty state when no items', () => {
    render(<TriageList items={[]} />);
    expect(screen.getByText(/all systems nominal/i)).toBeInTheDocument();
    expect(screen.getByText('0 items pending')).toBeInTheDocument();
  });

  it('renders item count correctly', () => {
    render(<TriageList items={mockItems} />);
    expect(screen.getByText('3 items pending')).toBeInTheDocument();
  });

  it('renders all triage item fields', () => {
    render(<TriageList items={mockItems} />);
    expect(screen.getByText('Sleep debt critical')).toBeInTheDocument();
    expect(screen.getByText('Hard stop at 10pm')).toBeInTheDocument();
    expect(screen.getByText('bio')).toBeInTheDocument();
    expect(screen.getByText('Laundry overdue')).toBeInTheDocument();
    expect(screen.getByText('Marcus: contact drift')).toBeInTheDocument();
    // Priority numbers
    expect(screen.getAllByText('9')).toHaveLength(1);
    expect(screen.getAllByText('6')).toHaveLength(2);
  });

  it('renders loading state with "Analyzing..." text', () => {
    render(<TriageList items={[]} isLoading={true} />);
    expect(screen.getByText('Analyzing...')).toBeInTheDocument();
  });

  it('renders triage items as semantic list items for screen readers', () => {
    render(<TriageList items={mockItems} />);
    const listItems = screen.getAllByRole('listitem');
    expect(listItems).toHaveLength(3);
  });
});
