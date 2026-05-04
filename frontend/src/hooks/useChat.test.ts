import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as client from '../api/client';
import type { StreamDonePayload } from '../types';

vi.mock('../api/client', () => ({
  fetchHistory: vi.fn(),
  completeTask: vi.fn(),
  completeSubtask: vi.fn(),
  streamCheckin: vi.fn(),
  fetchCheckin: vi.fn(),
  login: vi.fn(),
  fetchMe: vi.fn(),
  logout: vi.fn(),
  fetchDigest: vi.fn(),
  simulateWeek: vi.fn(),
}));

const mockFetchHistory = vi.mocked(client.fetchHistory);
const mockCompleteTask = vi.mocked(client.completeTask);
const mockStreamCheckin = vi.mocked(client.streamCheckin);

async function getHook() {
  const { useChat } = await import('./useChat');
  return useChat;
}

describe('useChat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal(
      'confirm',
      vi.fn(() => true)
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('token=null skips history fetch', async () => {
    const useChat = await getHook();
    renderHook(() => useChat(null));
    await vi.runAllTimersAsync().catch(vi.fn());
    expect(mockFetchHistory).not.toHaveBeenCalled();
  });

  it('fetchHistory rejects: logs error, does not throw', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(vi.fn());
    mockFetchHistory.mockRejectedValue(new Error('network error'));

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(consoleSpy).toHaveBeenCalledWith(expect.stringMatching(/hydrate/i), expect.any(Error));
    consoleSpy.mockRestore();
  });

  it('handleCompleteTask rejects: logs error, does not throw', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(vi.fn());
    mockFetchHistory.mockResolvedValue({ health: null as never, messages: [] });
    mockCompleteTask.mockRejectedValue(new Error('task API failure'));

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(() => result.current.handleCompleteTask('laundry'));

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringMatching(/complete task/i),
      expect.any(Error)
    );
    consoleSpy.mockRestore();
  });

  it('handleReset with ok=true clears health and messages', async () => {
    mockFetchHistory.mockResolvedValue({
      health: { overall_status: 'green' } as never,
      messages: [{ role: 'user', content: 'hello' }],
    });
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true }) as never)
    );

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(() => result.current.handleReset());

    expect(result.current.health).toBeNull();
    expect(result.current.messages).toHaveLength(0);
  });

  it('handleReset fetch throws: logs error, does not crash', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(vi.fn());
    mockFetchHistory.mockResolvedValue({ health: null as never, messages: [] });
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new Error('reset failed')))
    );

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(() => result.current.handleReset());

    expect(consoleSpy).toHaveBeenCalledWith(expect.stringMatching(/reset/i), expect.any(Error));
    consoleSpy.mockRestore();
  });

  it('isLoading clears when stream resolves without done event', async () => {
    mockFetchHistory.mockResolvedValue({ health: null as never, messages: [] });
    mockStreamCheckin.mockImplementation(
      (_c: unknown, _m: unknown, _t: unknown, _oA: unknown, onToken: (t: string) => void) => {
        onToken('partial response');
        return Promise.resolve();
      }
    );

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleSendMessage('hello');
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    const systemMsgs = result.current.messages.filter((m) => m.role === 'system');
    expect(systemMsgs[systemMsgs.length - 1]?.content).toBe('partial response');
  });

  it('handleSendMessage passes undefined token when hook token is null', async () => {
    mockStreamCheckin.mockImplementation(() => Promise.resolve());
    mockFetchHistory.mockResolvedValue({ health: null as never, messages: [] });

    const useChat = await getHook();
    const { result } = renderHook(() => useChat(null));

    act(() => {
      result.current.handleSendMessage('hello');
    });

    expect(mockStreamCheckin).toHaveBeenCalledWith(
      'hello',
      expect.any(Array),
      undefined,
      expect.any(Function),
      expect.any(Function),
      expect.any(Function),
      expect.any(Function)
    );
  });

  it('done with null responding_agent defaults to liaison in message', async () => {
    const doneDatum: StreamDonePayload = {
      responding_agent: null as never,
      contact_pauses: [],
      task_completions: [],
      active_pauses: [],
      behavioral_profiles: [],
      behavioral_summary: null,
    };
    mockFetchHistory.mockResolvedValue({ health: null as never, messages: [] });
    mockStreamCheckin.mockImplementation(
      (
        _c: unknown,
        _m: unknown,
        _t: unknown,
        _oA: unknown,
        onToken: (t: string) => void,
        onDone: (d: StreamDonePayload) => void
      ) => {
        onToken('Reply text');
        onDone(doneDatum);
        return Promise.resolve();
      }
    );

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleSendMessage('hello');
    });

    await waitFor(() => {
      const systemMsgs = result.current.messages.filter((m) => m.role === 'system');
      const last = systemMsgs[systemMsgs.length - 1] as { agent?: string };
      expect(last.agent).toBe('liaison');
    });
  });

  it('handleCompleteTask does not call fetchHistory when token is null', async () => {
    mockCompleteTask.mockResolvedValue(undefined);

    const useChat = await getHook();
    const { result } = renderHook(() => useChat(null));

    await act(() => result.current.handleCompleteTask('laundry'));

    expect(mockCompleteTask).toHaveBeenCalledWith('laundry', undefined);
    expect(mockFetchHistory).not.toHaveBeenCalled();
  });

  it('handleReset sends empty headers when token is null', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: true }) as never)
    );
    mockFetchHistory.mockResolvedValue({ health: null as never, messages: [] });

    const useChat = await getHook();
    const { result } = renderHook(() => useChat(null));

    await act(() => result.current.handleReset());

    const calls = (fetch as ReturnType<typeof vi.fn>).mock.calls;
    const lastCall = calls[calls.length - 1] as [string, RequestInit];
    expect(lastCall[1].headers).toEqual({});
  });

  it('clearSession resets all state', async () => {
    mockFetchHistory.mockResolvedValue({
      health: { overall_status: 'green' } as never,
      messages: [{ role: 'user', content: 'hi' }],
    });

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.clearSession();
    });

    expect(result.current.health).toBeNull();
    expect(result.current.messages).toHaveLength(0);
    expect(result.current.error).toBeNull();
  });

  it('done event with task_completions triggers fetchHistory refresh', async () => {
    const updatedHealth = { overall_status: 'green', triage_items: [] } as never;
    mockFetchHistory
      .mockResolvedValueOnce({ health: null as never, messages: [] }) // mount hydration
      .mockResolvedValueOnce({ health: updatedHealth, messages: [] }); // post-done refresh

    const doneDatum: StreamDonePayload = {
      responding_agent: 'logistics_fixer',
      contact_pauses: [],
      task_completions: ['laundry'],
      active_pauses: [],
      behavioral_profiles: [],
      behavioral_summary: null,
    };
    mockStreamCheckin.mockImplementation(
      (
        _c: unknown,
        _m: unknown,
        _t: unknown,
        _oA: unknown,
        onToken: (t: string) => void,
        onDone: (d: StreamDonePayload) => void
      ) => {
        onToken('Laundry is done!');
        onDone(doneDatum);
        return Promise.resolve();
      }
    );

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleSendMessage('laundry is done');
    });

    await waitFor(() => {
      expect(result.current.health).toEqual(updatedHealth);
    });
    expect(mockFetchHistory).toHaveBeenCalledTimes(2);
  });

  it('handleCompleteSubtask calls completeSubtask API and refreshes health', async () => {
    const updatedHealth = { overall_status: 'green' } as never;
    mockFetchHistory
      .mockResolvedValueOnce({ health: null as never, messages: [] })
      .mockResolvedValueOnce({ health: updatedHealth, messages: [] });
    vi.mocked(client.completeSubtask).mockResolvedValue(undefined);

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(() => result.current.handleCompleteSubtask('laundry', 'sort'));

    expect(vi.mocked(client.completeSubtask)).toHaveBeenCalledWith(
      'laundry',
      'sort',
      'valid-token'
    );
    expect(result.current.health).toEqual(updatedHealth);
  });

  it('handleCompleteSubtask logs error on failure', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(vi.fn());
    mockFetchHistory.mockResolvedValue({ health: null as never, messages: [] });
    vi.mocked(client.completeSubtask).mockRejectedValue(new Error('api error'));

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(() => result.current.handleCompleteSubtask('laundry', 'sort'));

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringMatching(/complete subtask/i),
      expect.any(Error)
    );
    consoleSpy.mockRestore();
  });

  it('done event without task_completions does not trigger extra fetchHistory', async () => {
    mockFetchHistory.mockResolvedValue({ health: null as never, messages: [] });

    const doneDatum: StreamDonePayload = {
      responding_agent: null as never,
      contact_pauses: [],
      task_completions: [],
      active_pauses: [],
      behavioral_profiles: [],
      behavioral_summary: null,
    };
    mockStreamCheckin.mockImplementation(
      (
        _c: unknown,
        _m: unknown,
        _t: unknown,
        _oA: unknown,
        onToken: (t: string) => void,
        onDone: (d: StreamDonePayload) => void
      ) => {
        onToken('All good!');
        onDone(doneDatum);
        return Promise.resolve();
      }
    );

    const useChat = await getHook();
    const { result } = renderHook(() => useChat('valid-token'));
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleSendMessage('checking in');
    });

    await waitFor(() => {
      const systemMsgs = result.current.messages.filter((m) => m.role === 'system');
      expect(systemMsgs.length).toBeGreaterThan(0);
    });

    // Only the mount hydration call — no second call for empty task_completions
    expect(mockFetchHistory).toHaveBeenCalledTimes(1);
  });
});
