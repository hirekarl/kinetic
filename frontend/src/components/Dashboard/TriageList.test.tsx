import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
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

// ── Task completion UI (Task A2) ─────────────────────────────────────────────

describe('TriageList — task completion', () => {
  const logisticsItemWithSource: TriageItem = {
    id: 'logistics-001',
    priority: 8,
    domain: 'logistics',
    description: 'Laundry critically overdue',
    action: 'Handle laundry today.',
    snooze_until: null,
    completed: false,
    source_id: 'laundry',
  };

  const logisticsItemNoSource: TriageItem = {
    id: 'logistics-002',
    priority: 5,
    domain: 'logistics',
    description: 'Dishes overdue',
    action: 'Handle dishes.',
    snooze_until: null,
    completed: false,
    source_id: null,
  };

  const bioItem: TriageItem = {
    id: 'bio-001',
    priority: 9,
    domain: 'bio',
    description: 'Sleep debt critical',
    action: 'Hard stop at 10pm',
    snooze_until: null,
    completed: false,
    source_id: null,
  };

  it('renders a complete button only for logistics items with a non-null source_id', () => {
    render(<TriageList items={[logisticsItemWithSource, logisticsItemNoSource, bioItem]} />);
    const completeButtons = screen.queryAllByRole('button', { name: /mark .* complete/i });
    expect(completeButtons).toHaveLength(1);
  });

  it('complete button has accessible aria-label including the task name', () => {
    render(<TriageList items={[logisticsItemWithSource]} />);
    expect(screen.getByRole('button', { name: /mark laundry complete/i })).toBeInTheDocument();
  });

  it('does not render a complete button for bio or relational items', () => {
    render(<TriageList items={[bioItem]} />);
    expect(screen.queryByRole('button', { name: /mark .* complete/i })).not.toBeInTheDocument();
  });

  it('handleComplete returns early when onCompleteTask is not provided', async () => {
    render(<TriageList items={[logisticsItemWithSource]} />);
    fireEvent.click(screen.getByRole('button', { name: /mark laundry complete/i }));
    // Item remains visible — no optimistic removal without handler
    await waitFor(() => {
      expect(screen.getByText('Laundry critically overdue')).toBeInTheDocument();
    });
  });

  it('calls onCompleteTask with source_id when button is clicked', async () => {
    const onCompleteTask = vi.fn().mockResolvedValue(undefined);
    render(<TriageList items={[logisticsItemWithSource]} onCompleteTask={onCompleteTask} />);
    fireEvent.click(screen.getByRole('button', { name: /mark laundry complete/i }));
    await waitFor(() => {
      expect(onCompleteTask).toHaveBeenCalledWith('laundry');
    });
  });

  it('optimistically removes the item from the list on click', async () => {
    const onCompleteTask = vi.fn().mockResolvedValue(undefined);
    render(<TriageList items={[logisticsItemWithSource]} onCompleteTask={onCompleteTask} />);
    fireEvent.click(screen.getByRole('button', { name: /mark laundry complete/i }));
    await waitFor(() => {
      expect(screen.queryByText('Laundry critically overdue')).not.toBeInTheDocument();
    });
  });

  it('restores the item if onCompleteTask rejects', async () => {
    const onCompleteTask = vi.fn().mockRejectedValue(new Error('Server error'));
    render(<TriageList items={[logisticsItemWithSource]} onCompleteTask={onCompleteTask} />);
    fireEvent.click(screen.getByRole('button', { name: /mark laundry complete/i }));
    await waitFor(() => {
      expect(screen.getByText('Laundry critically overdue')).toBeInTheDocument();
    });
  });
});
