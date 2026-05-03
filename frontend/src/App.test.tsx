import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
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
      source_id: null,
    },
  ],
  roi_summary: {
    time_recovered_minutes: 90,
    margin_recovered: '12% reclaimed',
    burnout_risk_delta: -5.0,
  },
  liaison_feedback: 'Focus on sleep first.',
  responding_agent: null,
  behavioral_profiles: [],
  behavioral_summary: null,
  active_pauses: [],
};

const MOCK_USER = { username: 'demo', tenant: 'demo', display_name: 'Demo' };

const mockFetchHistory = vi.fn();
const mockFetchCheckin = vi.fn();
const mockStreamCheckin = vi.fn();
const mockCompleteTask = vi.fn();
const mockFetchDigest = vi.fn();
const mockSimulateWeek = vi.fn();

vi.mock('./api/client', () => ({
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return
  fetchHistory: (...args: unknown[]) => mockFetchHistory(...args),
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return
  fetchCheckin: (...args: unknown[]) => mockFetchCheckin(...args),
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return
  streamCheckin: (...args: unknown[]) => mockStreamCheckin(...args),
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return
  completeTask: (...args: unknown[]) => mockCompleteTask(...args),
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return
  fetchDigest: (...args: unknown[]) => mockFetchDigest(...args),
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return
  simulateWeek: (...args: unknown[]) => mockSimulateWeek(...args),
  login: vi.fn(),
  fetchMe: vi.fn(),
  logout: vi.fn(),
}));

// Mock useAuth so these tests focus on dashboard behaviour, not auth flow
const mockUseAuth = vi.fn();
vi.mock('./hooks/useAuth', () => ({
  // eslint-disable-next-line @typescript-eslint/no-unsafe-return
  useAuth: () => mockUseAuth(),
}));

const defaultAuthState = {
  user: MOCK_USER,
  token: 'test-token',
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
};

const renderApp = (initialEntries = ['/app']) =>
  render(
    <MemoryRouter initialEntries={initialEntries}>
      <App />
    </MemoryRouter>
  );

describe('App — split-panel shell', () => {
  beforeEach(() => {
    mockFetchHistory.mockReset();
    mockFetchCheckin.mockReset();
    mockStreamCheckin.mockReset();
    mockCompleteTask.mockReset();
    mockFetchDigest.mockReset();
    mockSimulateWeek.mockReset();
    mockUseAuth.mockReturnValue(defaultAuthState);
    mockFetchHistory.mockResolvedValue({ health: null, messages: [] });
    mockStreamCheckin.mockResolvedValue(undefined);
    mockFetchDigest.mockResolvedValue({
      summary: 'Mock digest summary.',
      generated_at: new Date().toISOString(),
    });
    mockSimulateWeek.mockResolvedValue({ inserted: 5 });
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
    renderApp();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /operational liaison/i })).toBeInTheDocument();
    });
  });

  it('renders the dashboard panel heading', async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /mission control/i })).toBeInTheDocument();
    });
  });

  it('renders the initial idle state after history loads', async () => {
    renderApp();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /system idle/i })).toBeInTheDocument();
    });
  });

  it('populates the dashboard when history returns health data', async () => {
    mockFetchHistory.mockResolvedValue({ health: mockHealth, messages: [] });
    renderApp();
    await waitFor(() => {
      expect(screen.getByText('Sector Status')).toBeInTheDocument();
      expect(screen.getByText('Bio-Metric Archivist')).toBeInTheDocument();
      expect(screen.getByText('Logistics Fixer')).toBeInTheDocument();
      expect(screen.getByText('Relational Diplomat')).toBeInTheDocument();
    });
  });

  it('adds liaison feedback to the chat feed after a check-in', async () => {
    mockStreamCheckin.mockImplementation(
      (
        _msg: string,
        _hist: unknown,
        _tok: unknown,
        onAgents: (p: typeof mockHealth) => void,
        onToken: (t: string) => void,
        onDone: (d: unknown) => void
      ) => {
        onAgents(mockHealth);
        onToken('Focus on sleep first.');
        onDone({
          responding_agent: 'liaison',
          contact_pauses: [],
          task_completions: [],
          active_pauses: [],
          behavioral_profiles: [],
          behavioral_summary: null,
        });
      }
    );
    renderApp();
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
    renderApp();
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    fireEvent.click(screen.getByRole('button', { name: /reset system/i }));
    expect(window.confirm).toHaveBeenCalled();
  });

  // ── Error state — softened copy ────────────────────────────────────────────

  it('shows softened "Analysis unavailable" heading when check-in fails', async () => {
    mockStreamCheckin.mockImplementation(
      (
        _m: unknown,
        _h: unknown,
        _t: unknown,
        _oA: unknown,
        _oT: unknown,
        _oD: unknown,
        onError: (d: string) => void
      ) => {
        onError('Service unavailable');
      }
    );
    renderApp();
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText(/analysis unavailable/i)).toBeInTheDocument();
    });
  });

  it('does not use alarming "SYSTEM ERROR" copy in the error banner', async () => {
    mockStreamCheckin.mockImplementation(
      (
        _m: unknown,
        _h: unknown,
        _t: unknown,
        _oA: unknown,
        _oT: unknown,
        _oD: unknown,
        onError: (d: string) => void
      ) => {
        onError('Service unavailable');
      }
    );
    renderApp();
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.queryByText(/system error/i)).not.toBeInTheDocument();
    });
  });

  it('shows a Retry button in the error banner after a failed check-in', async () => {
    mockStreamCheckin.mockImplementation(
      (
        _m: unknown,
        _h: unknown,
        _t: unknown,
        _oA: unknown,
        _oT: unknown,
        _oD: unknown,
        onError: (d: string) => void
      ) => {
        onError('Service unavailable');
      }
    );
    renderApp();
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
    mockStreamCheckin
      .mockImplementationOnce(
        (
          _m: unknown,
          _h: unknown,
          _t: unknown,
          _oA: unknown,
          _oT: unknown,
          _oD: unknown,
          onError: (d: string) => void
        ) => {
          onError('Service unavailable');
        }
      )
      .mockImplementationOnce(
        (
          _msg: string,
          _hist: unknown,
          _tok: unknown,
          onAgents: (p: typeof mockHealth) => void,
          onToken: (t: string) => void,
          onDone: (d: unknown) => void
        ) => {
          onAgents(mockHealth);
          onToken('All systems restored.');
          onDone({
            responding_agent: 'liaison',
            contact_pauses: [],
            task_completions: [],
            active_pauses: [],
            behavioral_profiles: [],
            behavioral_summary: null,
          });
        }
      );

    renderApp();
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => screen.getByRole('button', { name: /retry/i }));

    await user.click(screen.getByRole('button', { name: /retry/i }));

    await waitFor(() => {
      expect(screen.queryByText(/analysis unavailable/i)).not.toBeInTheDocument();
      expect(mockStreamCheckin).toHaveBeenCalledTimes(2);
    });
  });

  it('error banner is absent when no error has occurred', async () => {
    renderApp();
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));
    expect(screen.queryByText(/analysis unavailable/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
  });

  it('chat feed shows softened error copy when check-in fails', async () => {
    mockStreamCheckin.mockImplementation(
      (
        _m: unknown,
        _h: unknown,
        _t: unknown,
        _oA: unknown,
        _oT: unknown,
        _oD: unknown,
        onError: (d: string) => void
      ) => {
        onError('Service unavailable');
      }
    );
    renderApp();
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.getByText(/check-in could not be processed/i)).toBeInTheDocument();
    });
  });

  it('chat feed does not use alarming "[CRITICAL ERROR]" prefix', async () => {
    mockStreamCheckin.mockImplementation(
      (
        _m: unknown,
        _h: unknown,
        _t: unknown,
        _oA: unknown,
        _oT: unknown,
        _oD: unknown,
        onError: (d: string) => void
      ) => {
        onError('Service unavailable');
      }
    );
    renderApp();
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));

    const textarea = screen.getByPlaceholderText(/what's your status/i);
    fireEvent.change(textarea, { target: { value: 'Slept 5 hours.' } });
    fireEvent.submit(textarea.closest('form')!);

    await waitFor(() => {
      expect(screen.queryByText(/critical error/i)).not.toBeInTheDocument();
    });
  });

  it('App calls completeTask API when a triage item complete button is clicked', async () => {
    const healthWithLogisticsItem = {
      ...mockHealth,
      triage_items: [
        {
          id: 'logistics-001',
          priority: 8,
          domain: 'logistics' as const,
          description: 'Laundry critically overdue',
          action: 'Handle laundry today.',
          snooze_until: null,
          completed: false,
          source_id: 'laundry',
        },
      ],
    };
    mockFetchHistory.mockResolvedValue({ health: healthWithLogisticsItem, messages: [] });
    mockCompleteTask.mockResolvedValue(undefined);

    renderApp();
    await waitFor(() => screen.getByRole('button', { name: /mark laundry complete/i }));

    fireEvent.click(screen.getByRole('button', { name: /mark laundry complete/i }));

    await waitFor(() => {
      expect(mockCompleteTask).toHaveBeenCalledWith('laundry', expect.anything());
    });
  });

  it('displays the authenticated user display name in the header', async () => {
    renderApp();
    await waitFor(() => screen.getByRole('heading', { name: /mission control/i }));
    expect(screen.getByText('Demo')).toBeInTheDocument();
  });

  it('renders a Sign out button in the header', async () => {
    renderApp();
    await waitFor(() => screen.getByRole('button', { name: /sign out/i }));
  });

  it('Sign out button calls authLogout and navigates away', async () => {
    const user = userEvent.setup();
    const mockLogout = vi.fn().mockResolvedValue(undefined);
    mockUseAuth.mockReturnValue({ ...defaultAuthState, logout: mockLogout });

    renderApp();
    await waitFor(() => screen.getByRole('button', { name: /sign out/i }));
    await user.click(screen.getByRole('button', { name: /sign out/i }));

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledOnce();
    });
  });

  // ── Simulate Week ──────────────────────────────────────────────────────────

  it('Simulate Week button is not rendered for non-demo tenant', async () => {
    mockUseAuth.mockReturnValue({
      ...defaultAuthState,
      user: { username: 'personal', tenant: 'personal', display_name: 'Personal' },
    });
    renderApp();
    await waitFor(() => screen.getByRole('heading', { name: /mission control/i }));
    expect(screen.queryByRole('button', { name: /simulate week/i })).not.toBeInTheDocument();
  });

  it('Simulate Week button is rendered for demo tenant', async () => {
    renderApp();
    await waitFor(() => screen.getByRole('button', { name: /simulate week/i }));
  });

  it('clicking Refresh in WeeklyDigestCard triggers handleRefreshDigest with force=true', async () => {
    mockFetchHistory.mockResolvedValue({ health: mockHealth, messages: [] });

    const user = userEvent.setup();
    renderApp();

    await waitFor(() => screen.getByText('Sector Status'));

    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    await user.click(screen.getByRole('button', { name: /^refresh$/i }));

    await waitFor(() => {
      expect(mockFetchDigest).toHaveBeenCalledWith(expect.anything(), true);
    });
  });

  it('Simulate Week does nothing when token is null', async () => {
    mockUseAuth.mockReturnValue({
      user: { username: 'demo', tenant: 'demo', display_name: 'Demo' },
      token: null,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderApp();
    await waitFor(() => screen.getByRole('button', { name: /simulate week/i }));

    fireEvent.click(screen.getByRole('button', { name: /simulate week/i }));

    expect(mockSimulateWeek).not.toHaveBeenCalled();
  });

  it('clicking Simulate Week calls simulateWeek then triggers a forced digest refresh', async () => {
    const user = userEvent.setup();
    renderApp();
    await waitFor(() => screen.getByRole('button', { name: /simulate week/i }));

    await user.click(screen.getByRole('button', { name: /simulate week/i }));

    await waitFor(() => {
      expect(mockSimulateWeek).toHaveBeenCalledTimes(1);
      expect(mockFetchDigest).toHaveBeenCalledWith(expect.anything(), true);
    });
  });

  it('clicking Simulate Week logs error when simulateWeek rejects', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(vi.fn());
    mockSimulateWeek.mockRejectedValueOnce(new Error('network error'));

    renderApp();
    await waitFor(() => screen.getByRole('button', { name: /simulate week/i }));

    fireEvent.click(screen.getByRole('button', { name: /simulate week/i }));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringMatching(/simulation failed/i),
        expect.any(Error)
      );
    });

    consoleSpy.mockRestore();
  });

  it('Simulate Week button is disabled while simulating', async () => {
    let resolveSimulate!: (v: { inserted: number }) => void;
    mockSimulateWeek.mockImplementation(
      () =>
        new Promise<{ inserted: number }>((resolve) => {
          resolveSimulate = resolve;
        })
    );

    renderApp();
    await waitFor(() => screen.getByRole('button', { name: /simulate week/i }));

    fireEvent.click(screen.getByRole('button', { name: /simulate week/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /simulating/i })).toBeDisabled();
    });

    // Resolve to allow test cleanup
    resolveSimulate({ inserted: 5 });
  });
});

// ── Onboarding ────────────────────────────────────────────────────────────────

describe('App — Onboarding', () => {
  let store: Map<string, string>;
  let mockLocalStorage: {
    getItem: ReturnType<typeof vi.fn>;
    setItem: ReturnType<typeof vi.fn>;
    removeItem: ReturnType<typeof vi.fn>;
  };

  beforeEach(() => {
    mockFetchHistory.mockReset();
    mockFetchCheckin.mockReset();
    mockStreamCheckin.mockReset();
    mockFetchDigest.mockReset();
    mockSimulateWeek.mockReset();
    mockStreamCheckin.mockResolvedValue(undefined);
    mockFetchHistory.mockResolvedValue({ health: null, messages: [] });
    mockFetchDigest.mockResolvedValue({
      summary: 'Mock digest summary.',
      generated_at: new Date().toISOString(),
    });
    mockSimulateWeek.mockResolvedValue({ inserted: 5 });
    mockUseAuth.mockReturnValue(defaultAuthState);
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
    renderApp();
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: /personal infrastructure/i })).toBeInTheDocument();
    });
  });

  it('does not show onboarding when kinetic_onboarded is already set', async () => {
    store.set('kinetic_onboarded', 'true');
    renderApp();
    await waitFor(() => screen.getByRole('heading', { name: /system idle/i }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('sets kinetic_onboarded in localStorage when onboarding is dismissed via Skip', async () => {
    renderApp();
    await waitFor(() => screen.getByRole('dialog'));
    fireEvent.click(screen.getByRole('button', { name: /skip/i }));
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('kinetic_onboarded', 'true');
  });

  it('modal disappears after Skip', async () => {
    renderApp();
    await waitFor(() => screen.getByRole('dialog'));
    fireEvent.click(screen.getByRole('button', { name: /skip/i }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});

// ── Auth gating ───────────────────────────────────────────────────────────────

describe('App — Auth gating', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', {
      getItem: vi.fn().mockReturnValue(null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the LoginScreen when user is null', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });
    renderApp(['/login']);
    expect(screen.getByRole('heading', { name: /^kinetic$/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
  });

  it('renders a loading spinner while authLoading is true', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: true,
      login: vi.fn(),
      logout: vi.fn(),
    });
    renderApp();
    // Neither the login screen heading nor the main app heading should be present
    expect(screen.queryByRole('heading', { name: /^kinetic$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: /mission control/i })).not.toBeInTheDocument();
  });

  it('shows the dashboard (not LoginScreen) when user is authenticated', async () => {
    mockFetchHistory.mockResolvedValue({ health: null, messages: [] });
    mockUseAuth.mockReturnValue(defaultAuthState);
    vi.stubGlobal('localStorage', {
      getItem: vi.fn().mockReturnValue('true'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
    renderApp();
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /mission control/i })).toBeInTheDocument();
    });
    expect(screen.queryByLabelText(/username/i)).not.toBeInTheDocument();
  });

  it('successful login navigates away from the login screen', async () => {
    const mockLogin = vi.fn().mockResolvedValue(undefined);
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: false,
      login: mockLogin,
      logout: vi.fn(),
    });
    const user = userEvent.setup();
    renderApp(['/login']);

    await user.type(screen.getByLabelText(/username/i), 'demo');
    await user.type(screen.getByLabelText(/password/i), 'password');
    await user.click(screen.getByRole('button', { name: /^sign in$/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('demo', 'password');
    });
    // After login, navigate('/app') is called — with null user the /app route redirects to LandingPage
    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: /your infrastructure is showing/i })
      ).toBeInTheDocument();
    });
  });

  it('login failure sets error message shown on LoginScreen', async () => {
    const mockLogin = vi.fn().mockRejectedValue(new Error('bad creds'));
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: false,
      login: mockLogin,
      logout: vi.fn(),
    });
    const user = userEvent.setup();
    renderApp(['/login']);
    await user.type(screen.getByLabelText(/username/i), 'demo');
    await user.type(screen.getByLabelText(/password/i), 'wrong');
    await user.click(screen.getByRole('button', { name: /^sign in$/i }));
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveTextContent(/invalid credentials/i);
    });
  });

  it('unauthenticated user navigating to /app is redirected to LandingPage', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });
    renderApp(['/app']);
    expect(
      screen.getByRole('heading', { name: /your infrastructure is showing/i })
    ).toBeInTheDocument();
    expect(screen.queryByLabelText(/username/i)).not.toBeInTheDocument();
  });

  it('authenticated user navigating to / is redirected to the dashboard', async () => {
    mockFetchHistory.mockResolvedValue({ health: null, messages: [] });
    mockFetchDigest.mockResolvedValue({ summary: 'x', generated_at: new Date().toISOString() });
    mockUseAuth.mockReturnValue(defaultAuthState);
    vi.stubGlobal('localStorage', {
      getItem: vi.fn().mockReturnValue('true'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
    renderApp(['/']);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /mission control/i })).toBeInTheDocument();
    });
  });

  it('authenticated user navigating to /login is redirected to the dashboard', async () => {
    mockFetchHistory.mockResolvedValue({ health: null, messages: [] });
    mockFetchDigest.mockResolvedValue({ summary: 'x', generated_at: new Date().toISOString() });
    mockUseAuth.mockReturnValue(defaultAuthState);
    vi.stubGlobal('localStorage', {
      getItem: vi.fn().mockReturnValue('true'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
    renderApp(['/login']);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /mission control/i })).toBeInTheDocument();
    });
  });

  it('wildcard route redirects unauthenticated user to LandingPage', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      token: null,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
    });
    renderApp(['/some/unknown/path']);
    expect(
      screen.getByRole('heading', { name: /your infrastructure is showing/i })
    ).toBeInTheDocument();
  });
});
