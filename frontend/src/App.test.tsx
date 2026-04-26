import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
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
    // Suppress onboarding so these tests stay focused on the dashboard shell
    vi.stubGlobal('localStorage', {
      getItem: vi.fn().mockReturnValue('true'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
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

  // ── Error state — softened copy ────────────────────────────────────────────

  it('shows softened "Analysis unavailable" heading when check-in fails', async () => {
    mockFetchCheckin.mockRejectedValue(new Error('Service unavailable'));
    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText(/analysis unavailable/i)).toBeInTheDocument();
    });
  });

  it('does not use alarming "SYSTEM ERROR" copy in the error banner', async () => {
    mockFetchCheckin.mockRejectedValue(new Error('Service unavailable'));
    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.queryByText(/system error/i)).not.toBeInTheDocument();
    });
  });

  it('shows a Retry button in the error banner after a failed check-in', async () => {
    mockFetchCheckin.mockRejectedValue(new Error('Service unavailable'));
    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });
  });

  it('Retry button re-submits the last message and clears the banner on success', async () => {
    const user = userEvent.setup();
    mockFetchCheckin
      .mockRejectedValueOnce(new Error('Service unavailable'))
      .mockResolvedValueOnce({ ...mockHealth, liaison_feedback: 'All systems restored.' });

    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => screen.getByRole('button', { name: /retry/i }));

    await user.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => {
      expect(screen.queryByText(/analysis unavailable/i)).not.toBeInTheDocument();
      expect(mockFetchCheckin).toHaveBeenCalledTimes(2);
    });
  });

  it('error banner is absent when no error has occurred', async () => {
    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));
    expect(screen.queryByText(/analysis unavailable/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });

  it('chat feed shows softened error copy when check-in fails', async () => {
    mockFetchCheckin.mockRejectedValue(new Error('Service unavailable'));
    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText(/check-in could not be processed/i)).toBeInTheDocument();
    });
  });

  it('chat feed does not use alarming "[CRITICAL ERROR]" prefix', async () => {
    mockFetchCheckin.mockRejectedValue(new Error('Service unavailable'));
    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.queryByText(/critical error/i)).not.toBeInTheDocument();
    });
  });
});

// ── Onboarding ────────────────────────────────────────────────────────────────

describe('App — Onboarding', () => {
  // Use a real in-memory store so we can test that setItem is called and
  // that subsequent getItem calls reflect the stored value.
  let store: Map<string, string>;
  let mockLocalStorage: {
    getItem: ReturnType<typeof vi.fn>;
    setItem: ReturnType<typeof vi.fn>;
    removeItem: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    mockFetchHistory.mockReset();
    mockFetchCheckin.mockReset();
    mockFetchHistory.mockResolvedValue({ health: null, messages: [] });
    store = new Map();
    mockLocalStorage = {
      getItem: vi.fn((key: string) => store.get(key) ?? null),
      setItem: vi.fn((key: string, value: string) => {
        store.set(key, value);
      }),
      removeItem: vi.fn((key: string) => {
        store.delete(key);
      }),
    };
    vi.stubGlobal('localStorage', mockLocalStorage);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows onboarding modal on first visit (no localStorage flag)', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /personal infrastructure/i })).toBeInTheDocument();
    });
  });

  it('does not show onboarding when kinetic_onboarded is already set', async () => {
    store.set('kinetic_onboarded', 'true');
    render(<App />);
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('sets kinetic_onboarded in localStorage when onboarding is dismissed via Skip', async () => {
    render(<App />);
    await waitFor(() => screen.getByRole('dialog'));
    fireEvent.click(screen.getByRole('button', { name: /skip/i }));
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('kinetic_onboarded', 'true');
  });

  it('modal disappears after Skip', async () => {
    render(<App />);
    await waitFor(() => screen.getByRole('dialog'));
    fireEvent.click(screen.getByRole('button', { name: /skip/i }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
