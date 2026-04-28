import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as client from '../api/client';

vi.mock('../api/client', () => ({
  login: vi.fn(),
  fetchMe: vi.fn(),
  logout: vi.fn(),
  fetchCheckin: vi.fn(),
  fetchHistory: vi.fn(),
  completeTask: vi.fn(),
  streamCheckin: vi.fn(),
}));

const mockLogin = vi.mocked(client.login);
const mockFetchMe = vi.mocked(client.fetchMe);
const mockLogout = vi.mocked(client.logout);

const MOCK_USER = { username: 'demo', tenant: 'demo', display_name: 'Demo' };

// Lazy import so vi.mock is set up before the module loads
async function getHook() {
  const { useAuth } = await import('./useAuth');
  return useAuth;
}

describe('useAuth', () => {
  let store: Map<string, string>;

  beforeEach(() => {
    vi.clearAllMocks();
    store = new Map();
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => store.get(key) ?? null),
      setItem: vi.fn((key: string, value: string) => {
        store.set(key, value);
      }),
      removeItem: vi.fn((key: string) => {
        store.delete(key);
      }),
      clear: vi.fn(() => {
        store.clear();
      }),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('initial state: isLoading=false, user=null, token=null when no localStorage token', async () => {
    const useAuth = await getHook();
    const { result } = renderHook(() => useAuth());
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
  });

  it('on mount with valid localStorage token: calls fetchMe and sets user', async () => {
    localStorage.setItem('kinetic_token', 'valid-token');
    mockFetchMe.mockResolvedValue(MOCK_USER);
    const useAuth = await getHook();
    const { result } = renderHook(() => useAuth());
    await waitFor(() => {
      expect(result.current.user).toEqual(MOCK_USER);
    });
    expect(mockFetchMe).toHaveBeenCalledWith('valid-token');
    expect(result.current.token).toBe('valid-token');
    expect(result.current.isLoading).toBe(false);
  });

  it('on mount with invalid token: clears localStorage, user remains null', async () => {
    localStorage.setItem('kinetic_token', 'bad-token');
    mockFetchMe.mockRejectedValue(new Error('401'));
    const useAuth = await getHook();
    const { result } = renderHook(() => useAuth());
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(localStorage.getItem('kinetic_token')).toBeNull();
  });

  it('login success: token stored in localStorage, user populated', async () => {
    mockLogin.mockResolvedValue({ access_token: 'new-token', tenant: 'demo' });
    mockFetchMe.mockResolvedValue(MOCK_USER);
    const useAuth = await getHook();
    const { result } = renderHook(() => useAuth());
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    await act(() => result.current.login('demo', 'password'));
    expect(localStorage.getItem('kinetic_token')).toBe('new-token');
    expect(result.current.user).toEqual(MOCK_USER);
    expect(result.current.token).toBe('new-token');
  });

  it('login failure: throws, user remains null', async () => {
    mockLogin.mockRejectedValue(new Error('Invalid credentials'));
    const useAuth = await getHook();
    const { result } = renderHook(() => useAuth());
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    await expect(act(() => result.current.login('demo', 'wrong'))).rejects.toThrow();
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
  });

  it('logout: calls API, clears localStorage, user=null and token=null', async () => {
    localStorage.setItem('kinetic_token', 'valid-token');
    mockFetchMe.mockResolvedValue(MOCK_USER);
    mockLogout.mockResolvedValue(undefined);
    const useAuth = await getHook();
    const { result } = renderHook(() => useAuth());
    await waitFor(() => {
      expect(result.current.user).toEqual(MOCK_USER);
    });
    await act(() => result.current.logout());
    expect(mockLogout).toHaveBeenCalledWith('valid-token');
    expect(localStorage.getItem('kinetic_token')).toBeNull();
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
  });
});
