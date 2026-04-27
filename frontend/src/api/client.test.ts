import { vi, describe, it, expect, beforeEach } from 'vitest';
import { fetchCheckin, fetchHistory, completeTask, login, fetchMe, logout } from './client';

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

    it('includes Authorization header when token is provided', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
      await fetchCheckin('test', [], 'my-token');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/checkin'),
        expect.objectContaining({
          headers: { 'Content-Type': 'application/json', Authorization: 'Bearer my-token' },
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
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/history'),
        expect.objectContaining({ headers: {} })
      );
    });

    it('includes Authorization header when token is provided', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
      await fetchHistory('my-token');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/history'),
        expect.objectContaining({ headers: { Authorization: 'Bearer my-token' } })
      );
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

  describe('completeTask', () => {
    it('sends PATCH to /api/tasks/:name/complete', async () => {
      mockFetch.mockResolvedValue({ ok: true });
      await completeTask('laundry');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tasks/laundry/complete'),
        expect.objectContaining({ method: 'PATCH' })
      );
    });

    it('includes Authorization header when token is provided', async () => {
      mockFetch.mockResolvedValue({ ok: true });
      await completeTask('laundry', 'my-token');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({ headers: { Authorization: 'Bearer my-token' } })
      );
    });
  });

  describe('login', () => {
    it('POSTs credentials and returns access_token + tenant', async () => {
      const mockResponse = { access_token: 'tok', tenant: 'demo' };
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockResponse) });

      const result = await login('demo', 'password');
      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/login'),
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('throws on 401 with detail message', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Invalid credentials' }),
      });
      await expect(login('bad', 'bad')).rejects.toThrow('Invalid credentials');
    });
  });

  describe('fetchMe', () => {
    it('GETs /api/auth/me with Bearer token and returns AuthUser', async () => {
      const mockUser = { username: 'demo', tenant: 'demo', display_name: 'Demo' };
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockUser) });

      const result = await fetchMe('my-token');
      expect(result).toEqual(mockUser);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/me'),
        expect.objectContaining({ headers: { Authorization: 'Bearer my-token' } })
      );
    });

    it('throws on non-ok response', async () => {
      mockFetch.mockResolvedValue({ ok: false });
      await expect(fetchMe('bad')).rejects.toThrow('Not authenticated');
    });
  });

  describe('logout', () => {
    it('POSTs to /api/auth/logout with Bearer token', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ status: 'ok' }) });
      await logout('my-token');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/logout'),
        expect.objectContaining({
          method: 'POST',
          headers: { Authorization: 'Bearer my-token' },
        })
      );
    });
  });
});
