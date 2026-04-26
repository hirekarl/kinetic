import { vi, describe, it, expect, beforeEach } from 'vitest';
import { fetchCheckin, fetchHistory } from './client';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

describe('API client', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  describe('fetchCheckin', () => {
    it('sends a POST to /api/checkin with the message and history', async () => {
      const mockPayload = { overall_status: 'green' };
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockPayload) });

      const result = await fetchCheckin('I slept 8 hours.', []);
      expect(result).toEqual(mockPayload);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/checkin'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });

    it('uses empty history when not provided', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
      await fetchCheckin('test message');
      const body = JSON.parse(
        (mockFetch.mock.calls[0] as [string, RequestInit])[1].body as string
      ) as { history: unknown[]; message: string };
      expect(body.history).toEqual([]);
    });

    it('throws an error with detail message on non-ok response', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Service Unavailable',
        json: () => Promise.resolve({ detail: 'Gemini API is down' }),
      });
      await expect(fetchCheckin('test')).rejects.toThrow('Gemini API is down');
    });

    it('falls back to statusText when error response has no detail', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Internal Server Error',
        json: () => Promise.reject(new Error('parse failed')),
      });
      await expect(fetchCheckin('test')).rejects.toThrow('Internal Server Error');
    });
  });

  describe('fetchHistory', () => {
    it('sends a GET to /api/history and returns parsed JSON', async () => {
      const mockPayload = { health: null, messages: [] };
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockPayload) });

      const result = await fetchHistory();
      expect(result).toEqual(mockPayload);
      expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/api/history'));
    });

    it('throws on non-ok response', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Not Found',
        json: () => Promise.resolve({}),
      });
      await expect(fetchHistory()).rejects.toThrow('Failed to fetch system history.');
    });
  });
});
