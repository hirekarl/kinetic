import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as client from '../api/client';

vi.mock('../api/client', () => ({
  fetchDigest: vi.fn(),
  fetchHistory: vi.fn(),
  completeTask: vi.fn(),
  streamCheckin: vi.fn(),
  fetchCheckin: vi.fn(),
  login: vi.fn(),
  fetchMe: vi.fn(),
  logout: vi.fn(),
  simulateWeek: vi.fn(),
}));

const mockFetchDigest = vi.mocked(client.fetchDigest);

async function getHook() {
  const { useDigest } = await import('./useDigest');
  return useDigest;
}

const MOCK_DIGEST = { summary: 'Your 14-day digest.', generated_at: '2026-05-01T12:00:00' };

describe('useDigest', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initial fetch with token: calls fetchDigest and populates digestData', async () => {
    mockFetchDigest.mockResolvedValue(MOCK_DIGEST);
    const useDigest = await getHook();
    const { result } = renderHook(() => useDigest('valid-token'));

    await waitFor(() => {
      expect(result.current.digestData).toEqual(MOCK_DIGEST);
    });
    expect(mockFetchDigest).toHaveBeenCalledWith('valid-token');
  });

  it('initial fetch error: logs error, digestData remains null', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(vi.fn());
    mockFetchDigest.mockRejectedValue(new Error('API unavailable'));

    const useDigest = await getHook();
    const { result } = renderHook(() => useDigest('valid-token'));

    await waitFor(() => {
      expect(result.current.digestLoading).toBe(false);
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringMatching(/fetch digest/i),
      expect.any(Error)
    );
    expect(result.current.digestData).toBeNull();
    consoleSpy.mockRestore();
  });

  it('handleRefreshDigest success: updates digestData with force=true result', async () => {
    const fresh = { summary: 'Refreshed digest.', generated_at: '2026-05-02T12:00:00' };
    mockFetchDigest.mockResolvedValueOnce(MOCK_DIGEST).mockResolvedValueOnce(fresh);

    const useDigest = await getHook();
    const { result } = renderHook(() => useDigest('valid-token'));
    await waitFor(() => {
      expect(result.current.digestData).toEqual(MOCK_DIGEST);
    });

    await act(() => result.current.handleRefreshDigest());

    expect(result.current.digestData).toEqual(fresh);
    expect(mockFetchDigest).toHaveBeenCalledWith('valid-token', true);
  });

  it('handleRefreshDigest error: logs error, does not crash', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(vi.fn());
    mockFetchDigest
      .mockResolvedValueOnce(MOCK_DIGEST)
      .mockRejectedValueOnce(new Error('refresh failed'));

    const useDigest = await getHook();
    const { result } = renderHook(() => useDigest('valid-token'));
    await waitFor(() => {
      expect(result.current.digestData).toEqual(MOCK_DIGEST);
    });

    await act(() => result.current.handleRefreshDigest());

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringMatching(/refresh digest/i),
      expect.any(Error)
    );
    consoleSpy.mockRestore();
  });

  it('handleRefreshDigest does nothing when token is null', async () => {
    const useDigest = await getHook();
    const { result } = renderHook(() => useDigest(null));

    await act(() => result.current.handleRefreshDigest());

    expect(mockFetchDigest).not.toHaveBeenCalled();
  });

  it('clearDigest: sets digestData to null', async () => {
    mockFetchDigest.mockResolvedValue(MOCK_DIGEST);

    const useDigest = await getHook();
    const { result } = renderHook(() => useDigest('valid-token'));
    await waitFor(() => {
      expect(result.current.digestData).toEqual(MOCK_DIGEST);
    });

    act(() => {
      result.current.clearDigest();
    });

    expect(result.current.digestData).toBeNull();
  });
});
