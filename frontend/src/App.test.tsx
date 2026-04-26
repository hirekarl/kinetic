import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from './App';
import { SystemHealthPayload } from './types';

const mockHealth: SystemHealthPayload = {
  overall_status: 'yellow',
  bio: {
    status: 'yellow',
    burnout_score: 62,
    forecast: 'Sleep deficit increasing.',
    sleep_debt_hours: 3,
    recommendations: ['Hard stop at 11pm'],
  },
  logistics: {
    status: 'yellow',
    critical_tasks: ['laundry'],
    tasks_with_steps: [],
    outsourcing_suggestions: [],
    time_to_resolve_minutes: 90,
  },
  relational: {
    status: 'yellow',
    connection_margin_score: 60,
    at_risk_relationships: ['Marcus'],
    interaction_sprints: ['Send Marcus a check-in today.'],
  },
  triage_items: [
    {
      id: 'bio-001',
      priority: 6,
      domain: 'bio',
      description: 'Sleep debt accumulating',
      action: 'Hard stop at 11pm',
      snooze_until: null,
      completed: false,
    },
  ],
  roi_summary: {
    time_recovered_minutes: 90,
    margin_recovered: '12% reclaimed',
    burnout_risk_delta: -5.0,
  },
  liaison_feedback: 'Focus on sleep first.',
  behavioral_profiles: [],
};

const mockFetchHistory = vi.fn();
const mockFetchCheckin = vi.fn();

vi.mock('./api/client', () => ({
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return
  fetchHistory: () => mockFetchHistory(),
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return
  fetchCheckin: (...args: unknown[]) => mockFetchCheckin(...args),
}));

describe('App — split-panel shell', () => {
  beforeEach(() => {
    mockFetchHistory.mockReset();
    mockFetchCheckin.mockReset();
    mockFetchHistory.mockResolvedValue({ health: null, messages: [] });
  });

  it('renders the chat panel heading', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /operational liaison/i })).toBeInTheDocument();
    });
  });

  it('renders the dashboard panel heading', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /mission control/i })).toBeInTheDocument();
    });
  });

  it('renders the initial idle state after history loads', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /system idle/i })).toBeInTheDocument();
    });
  });

  it('populates the dashboard when history returns health data', async () => {
    mockFetchHistory.mockResolvedValue({ health: mockHealth, messages: [] });
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('Sector Status')).toBeInTheDocument();
      expect(screen.getByText('Bio-Metric Archivist')).toBeInTheDocument();
      expect(screen.getByText('Logistics Fixer')).toBeInTheDocument();
      expect(screen.getByText('Relational Diplomat')).toBeInTheDocument();
    });
  });

  it('adds liaison feedback to the chat feed after a check-in', async () => {
    mockFetchCheckin.mockResolvedValue(mockHealth);
    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText('Focus on sleep first.')).toBeInTheDocument();
    });
  });

  it('prompts for confirmation when Reset System is clicked', async () => {
    vi.stubGlobal('confirm', vi.fn().mockReturnValue(false));
    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    fireEvent.click(screen.getByRole('button', { name: /reset system/i }));
    expect(window.confirm).toHaveBeenCalled();
  });

  it('shows error message when check-in fails', async () => {
    mockFetchCheckin.mockRejectedValue(new Error('Service unavailable'));
    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Test.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText(/system error/i)).toBeInTheDocument();
    });
  });
});
