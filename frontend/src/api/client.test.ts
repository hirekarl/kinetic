import { vi, describe, it, expect, beforeEach } from 'vitest';
import {
  fetchCheckin,
  fetchHistory,
  completeTask,
  login,
  fetchMe,
  logout,
  streamCheckin,
  simulateWeek,
  fetchDigest,
} from './client';
import type { SystemHealthPayload, StreamDonePayload } from '../types';

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

    it('uses default message when json parses but has no detail field', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: 'Bad Request',
        json: () => Promise.resolve({}),
      });
      await expect(fetchCheckin('test')).rejects.toThrow('An unexpected error occurred.');
    });

    it('uses default message when statusText is empty and json parse fails', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        statusText: '',
        json: () => Promise.reject(new Error('parse failed')),
      });
      await expect(fetchCheckin('test')).rejects.toThrow('An unexpected error occurred.');
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

    it('throws on non-ok response', async () => {
      mockFetch.mockResolvedValue({ ok: false, statusText: 'Not Found' });
      await expect(completeTask('unknown')).rejects.toThrow("Failed to complete task 'unknown'");
    });
  });

  describe('simulateWeek', () => {
    it('sends POST to /api/demo/simulate and returns inserted count', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ inserted: 5 }) });
      const result = await simulateWeek('my-token');
      expect(result).toEqual({ inserted: 5 });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/demo/simulate'),
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('throws on non-ok response', async () => {
      mockFetch.mockResolvedValue({ ok: false });
      await expect(simulateWeek()).rejects.toThrow('Failed to run simulation.');
    });
  });

  describe('fetchDigest', () => {
    it('sends GET to /api/digest and returns digest data', async () => {
      const mockDigest = { summary: 'Weekly review.', generated_at: '2026-05-01T12:00:00' };
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockDigest) });
      const result = await fetchDigest('my-token');
      expect(result).toEqual(mockDigest);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/digest'),
        expect.objectContaining({ headers: { Authorization: 'Bearer my-token' } })
      );
    });

    it('appends ?force=true when force parameter is true', async () => {
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
      await fetchDigest(undefined, true);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('?force=true'),
        expect.anything()
      );
    });

    it('throws on non-ok response', async () => {
      mockFetch.mockResolvedValue({ ok: false });
      await expect(fetchDigest()).rejects.toThrow('Failed to fetch digest.');
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

    it('falls back to default message when error response body is not JSON', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.reject(new Error('parse failed')),
      });
      await expect(login('bad', 'bad')).rejects.toThrow('Invalid credentials.');
    });

    it('uses default message when json parses but has no detail field', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({}),
      });
      await expect(login('bad', 'bad')).rejects.toThrow('Invalid credentials.');
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

  describe('streamCheckin', () => {
    const mockHealth: SystemHealthPayload = {
      overall_status: 'green',
      bio: null,
      logistics: null,
      relational: null,
      triage_items: [],
      roi_summary: null,
      liaison_feedback: null,
      responding_agent: null,
      behavioral_profiles: [],
      behavioral_summary: null,
      active_pauses: [],
    };

    const mockDone: StreamDonePayload = {
      responding_agent: 'liaison',
      contact_pauses: [],
      task_completions: [],
      active_pauses: [],
      behavioral_profiles: [],
      behavioral_summary: null,
    };

    function makeSSEStream(events: { event: string; data: string }[]): ReadableStream<Uint8Array> {
      const encoder = new TextEncoder();
      const text = events.map(({ event, data }) => `event: ${event}\ndata: ${data}\n\n`).join('');
      return new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(text));
          controller.close();
        },
      });
    }

    const noop = vi.fn();

    beforeEach(() => {
      noop.mockClear();
    });

    it('sends POST to /api/checkin/stream with auth header', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: makeSSEStream([
          { event: 'agents', data: JSON.stringify(mockHealth) },
          { event: 'done', data: JSON.stringify(mockDone) },
        ]),
      });

      await streamCheckin('hello', [], 'test-token', noop, noop, noop, noop);

      const [url, opts] = mockFetch.mock.calls[0] as [string, RequestInit];
      expect(url).toContain('/api/checkin/stream');
      expect((opts.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
      expect(opts.method).toBe('POST');
    });

    it('calls onAgents when agents event fires', async () => {
      const onAgents = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: makeSSEStream([
          { event: 'agents', data: JSON.stringify(mockHealth) },
          { event: 'done', data: JSON.stringify(mockDone) },
        ]),
      });

      await streamCheckin('hello', [], undefined, onAgents, noop, noop, noop);

      expect(onAgents).toHaveBeenCalledOnce();
      expect(onAgents).toHaveBeenCalledWith(expect.objectContaining({ overall_status: 'green' }));
    });

    it('calls onToken for each token event', async () => {
      const onToken = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: makeSSEStream([
          { event: 'agents', data: JSON.stringify(mockHealth) },
          { event: 'token', data: JSON.stringify({ text: 'Hello ' }) },
          { event: 'token', data: JSON.stringify({ text: 'world.' }) },
          { event: 'done', data: JSON.stringify(mockDone) },
        ]),
      });

      await streamCheckin('hello', [], undefined, noop, onToken, noop, noop);

      expect(onToken).toHaveBeenCalledTimes(2);
      expect(onToken).toHaveBeenNthCalledWith(1, 'Hello ');
      expect(onToken).toHaveBeenNthCalledWith(2, 'world.');
    });

    it('calls onDone with StreamDonePayload on done event', async () => {
      const onDone = vi.fn();
      const done: StreamDonePayload = { ...mockDone, responding_agent: 'bio_archivist' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: makeSSEStream([
          { event: 'agents', data: JSON.stringify(mockHealth) },
          { event: 'done', data: JSON.stringify(done) },
        ]),
      });

      await streamCheckin('hello', [], undefined, noop, noop, onDone, noop);

      expect(onDone).toHaveBeenCalledOnce();
      expect(onDone).toHaveBeenCalledWith(
        expect.objectContaining({ responding_agent: 'bio_archivist' })
      );
    });

    it('calls onError on error event', async () => {
      const onError = vi.fn();
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: makeSSEStream([{ event: 'error', data: JSON.stringify({ detail: 'LLM failure' }) }]),
      });

      await streamCheckin('hello', [], undefined, noop, noop, noop, onError);

      expect(onError).toHaveBeenCalledOnce();
      expect(onError).toHaveBeenCalledWith('LLM failure');
    });

    it('falls back to fetchCheckin on non-200 response', async () => {
      const onAgents = vi.fn();
      const onToken = vi.fn();
      const onDone = vi.fn();
      mockFetch
        .mockResolvedValueOnce({ ok: false, status: 503, body: null })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ ...mockHealth, liaison_feedback: 'Fallback response' }),
        });

      await streamCheckin('hello', [], 'tok', onAgents, onToken, onDone, noop);

      expect(onAgents).toHaveBeenCalledOnce();
      expect(onToken).toHaveBeenCalledWith('Fallback response');
      expect(onDone).toHaveBeenCalledOnce();
    });

    it('falls back to fetchCheckin on network error', async () => {
      const onAgents = vi.fn();
      const onDone = vi.fn();
      mockFetch.mockRejectedValueOnce(new TypeError('Network error')).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockHealth),
      });

      await streamCheckin('hello', [], undefined, onAgents, noop, onDone, noop);

      expect(onAgents).toHaveBeenCalledOnce();
      expect(onDone).toHaveBeenCalledOnce();
    });

    it('calls onError when fallback fetchCheckin also fails', async () => {
      const onError = vi.fn();
      // First call (SSE stream) fails → triggers fallback
      // Second call (fetchCheckin in fallback) also fails
      mockFetch
        .mockResolvedValueOnce({ ok: false, status: 503, body: null })
        .mockResolvedValueOnce({
          ok: false,
          statusText: 'Service Unavailable',
          json: () => Promise.resolve({ detail: 'API down' }),
        });

      await streamCheckin('hello', [], 'tok', noop, noop, noop, onError);

      expect(onError).toHaveBeenCalledWith('API down');
    });

    it('uses "Failed to connect." when fallback throws a non-Error value', async () => {
      const onError = vi.fn();
      mockFetch
        .mockResolvedValueOnce({ ok: false, status: 503, body: null })
        .mockRejectedValueOnce('string error');

      await streamCheckin('hello', [], 'tok', noop, noop, noop, onError);

      expect(onError).toHaveBeenCalledWith('Failed to connect.');
    });
  });
});
