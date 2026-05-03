import { useState, useEffect } from 'react';
import { fetchDigest } from '../api/client';
import type { DigestResponse } from '../types';

/**
 * Return shape of the `useDigest` hook, exposing digest data, loading flags,
 * and a force-refresh action.
 */
interface UseDigestReturn {
  digestData: DigestResponse | null;
  digestLoading: boolean;
  digestRefreshing: boolean;
  handleRefreshDigest: () => Promise<void>;
  clearDigest: () => void;
}

/**
 * Fetches the weekly AI-generated digest on mount and exposes a force-refresh action.
 *
 * The initial fetch is skipped when `token` is null (unauthenticated). The
 * `handleRefreshDigest` action sets `digestRefreshing` (not `digestLoading`) so
 * the card UI can distinguish initial load from a user-triggered refresh.
 *
 * @param token - JWT access token; when `null` no fetch is attempted.
 * @returns `UseDigestReturn` with digest data, loading/refreshing flags, and actions.
 */
export function useDigest(token: string | null): UseDigestReturn {
  const [digestData, setDigestData] = useState<DigestResponse | null>(null);
  const [digestLoading, setDigestLoading] = useState(false);
  const [digestRefreshing, setDigestRefreshing] = useState(false);

  useEffect(() => {
    if (!token) return;
    setDigestLoading(true);
    void fetchDigest(token)
      .then((data) => {
        setDigestData(data);
      })
      .catch((err: unknown) => {
        console.error('Failed to fetch digest', err);
      })
      .finally(() => {
        setDigestLoading(false);
      });
  }, [token]);

  const handleRefreshDigest = async (): Promise<void> => {
    if (!token) return;
    setDigestRefreshing(true);
    try {
      const data = await fetchDigest(token, true);
      setDigestData(data);
    } catch (err) {
      console.error('Failed to refresh digest', err);
    } finally {
      setDigestRefreshing(false);
    }
  };

  const clearDigest = () => {
    setDigestData(null);
  };

  return {
    digestData,
    digestLoading,
    digestRefreshing,
    handleRefreshDigest,
    clearDigest,
  };
}
