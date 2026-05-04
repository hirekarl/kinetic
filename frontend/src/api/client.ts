import { AuthUser, DigestResponse, StreamDonePayload, SystemHealthPayload } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Builds an Authorization header object from an optional JWT token.
 *
 * @param token - JWT access token. Returns an empty object when omitted so
 *   callers can spread the result unconditionally.
 * @returns A header record with the Bearer token, or an empty object.
 */
function authHeaders(token?: string): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Posts a check-in message to the blocking `/api/checkin` endpoint.
 *
 * @param message - Free-text check-in message from the user.
 * @param history - Prior conversation turns for multi-turn context.
 * @param token - Optional JWT for authenticated requests.
 * @returns The parsed `SystemHealthPayload` from the orchestrator.
 */
export async function fetchCheckin(
  message: string,
  history: { role: string; content: string }[] = [],
  token?: string
): Promise<SystemHealthPayload> {
  const response = await fetch(`${API_BASE_URL}/api/checkin`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(token),
    },
    body: JSON.stringify({ message, history }),
  });

  if (!response.ok) {
    let errorMessage = 'An unexpected error occurred.';
    try {
      const errorData = (await response.json()) as { detail?: string };
      errorMessage = errorData.detail ?? errorMessage;
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  return response.json() as Promise<SystemHealthPayload>;
}

/**
 * Triggers the demo week simulation, inserting pre-scripted historical check-ins.
 *
 * @param token - Optional JWT; only the `demo` tenant is permitted by the server.
 * @returns An object with the count of rows inserted.
 */
export async function simulateWeek(token?: string): Promise<{ inserted: number }> {
  const response = await fetch(`${API_BASE_URL}/api/demo/simulate`, {
    method: 'POST',
    headers: authHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Failed to run simulation.');
  }
  return response.json() as Promise<{ inserted: number }>;
}

/**
 * Fetches the AI-generated weekly digest summary.
 *
 * @param token - Optional JWT for authenticated requests.
 * @param force - When `true`, bypasses the 6-hour server-side cache.
 * @returns The `DigestResponse` containing the prose summary and generation timestamp.
 */
export async function fetchDigest(token?: string, force?: boolean): Promise<DigestResponse> {
  const url = `${API_BASE_URL}/api/digest${force ? '?force=true' : ''}`;
  const response = await fetch(url, {
    headers: authHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch digest.');
  }
  return response.json() as Promise<DigestResponse>;
}

/**
 * Marks a logistics task complete via `PATCH /api/tasks/:taskName/complete`.
 *
 * @param taskName - The task's `source_id` as returned in `TriageItem`.
 * @param token - Optional JWT for authenticated requests.
 */
export async function completeTask(taskName: string, token?: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/tasks/${encodeURIComponent(taskName)}/complete`,
    { method: 'PATCH', headers: authHeaders(token) }
  );
  if (!response.ok) {
    throw new Error(`Failed to complete task '${taskName}': ${response.statusText}`);
  }
}

/**
 * Marks a single subtask as completed within the named parent task.
 *
 * @param taskName - The parent task name.
 * @param subtaskName - The subtask step to mark complete.
 * @param token - Optional JWT for authenticated requests.
 */
export async function completeSubtask(
  taskName: string,
  subtaskName: string,
  token?: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/tasks/${encodeURIComponent(taskName)}/subtasks`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
      body: JSON.stringify({ subtask: subtaskName }),
    }
  );
  if (!response.ok) {
    throw new Error(`Failed to complete subtask '${subtaskName}': ${response.statusText}`);
  }
}

/**
 * Retrieves the most recent check-in snapshot and reconstructed message history.
 *
 * @param token - Optional JWT for authenticated requests.
 * @returns An object containing the latest `SystemHealthPayload` and the
 *   conversation message list used to hydrate the chat panel on page load.
 */
export async function fetchHistory(token?: string): Promise<{
  health: SystemHealthPayload;
  messages: { role: 'user' | 'system'; content: string }[];
}> {
  const response = await fetch(`${API_BASE_URL}/api/history`, {
    headers: authHeaders(token),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch system history.');
  }

  return response.json() as Promise<{
    health: SystemHealthPayload;
    messages: { role: 'user' | 'system'; content: string }[];
  }>;
}

/**
 * Authenticates with username and password, returning a JWT access token.
 *
 * @param username - Tenant username from `credentials.toml`.
 * @param password - Plaintext password (bcrypt-verified server-side).
 * @returns An object with `access_token` and the resolved `tenant` name.
 */
export async function login(
  username: string,
  password: string
): Promise<{ access_token: string; tenant: string }> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    let errorMessage = 'Invalid credentials.';
    try {
      const data = (await response.json()) as { detail?: string };
      errorMessage = data.detail ?? errorMessage;
    } catch {
      // ignore parse failure
    }
    throw new Error(errorMessage);
  }
  return response.json() as Promise<{ access_token: string; tenant: string }>;
}

/**
 * Validates a stored JWT and returns the current user's profile.
 *
 * @param token - JWT access token to validate.
 * @returns The `AuthUser` bound to the token, or throws if the token is invalid.
 */
export async function fetchMe(token: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error('Not authenticated');
  }
  return response.json() as Promise<AuthUser>;
}

/**
 * Revokes the current session by calling the server-side logout endpoint.
 *
 * @param token - JWT access token to invalidate.
 */
export async function logout(token: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/auth/logout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

/**
 * Opens a Server-Sent Events stream against `/api/checkin/stream` and dispatches
 * parsed events to the provided callbacks as they arrive.
 *
 * The SSE protocol yields three event types in order:
 * - `agents` — fired once when all specialist agents complete; carries the full
 *   `SystemHealthPayload` so the dashboard can render immediately.
 * - `token` — fired once per streamed text chunk from the Operational Liaison.
 * - `done` — fired when the stream closes; carries `StreamDonePayload` with
 *   metadata such as `responding_agent`, `contact_pauses`, and `task_completions`.
 *
 * EventSource is not used here because it cannot POST or send Authorization headers.
 * Instead, `fetch` + `ReadableStream` is used to manually parse the SSE wire format.
 * If the initial fetch fails or the server returns a non-2xx response, the function
 * falls back to the blocking `fetchCheckin` endpoint and synthesises equivalent callbacks.
 *
 * @param message - Free-text check-in message from the user.
 * @param history - Prior conversation turns for multi-turn context.
 * @param token - Optional JWT for authenticated requests.
 * @param onAgents - Called with the `SystemHealthPayload` once agents complete.
 * @param onToken - Called for each incremental text token from the liaison.
 * @param onDone - Called with the `StreamDonePayload` when the stream closes.
 * @param onError - Called with an error detail string if the stream or fallback fails.
 */
export async function streamCheckin(
  message: string,
  history: { role: string; content: string }[] = [],
  token: string | undefined,
  onAgents: (payload: SystemHealthPayload) => void,
  onToken: (text: string) => void,
  onDone: (payload: StreamDonePayload) => void,
  onError: (detail: string) => void
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/checkin/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
      body: JSON.stringify({ message, history }),
    });
  } catch {
    return _fallback(message, history, token, onAgents, onToken, onDone, onError);
  }

  if (!response.ok || !response.body) {
    return _fallback(message, history, token, onAgents, onToken, onDone, onError);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let currentEvent = '';

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';
      for (const line of lines) {
        const trimmed = line.trimEnd();
        if (trimmed.startsWith('event:')) {
          currentEvent = trimmed.slice(6).trim();
        } else if (trimmed.startsWith('data:')) {
          const raw = trimmed.slice(5).trim();
          switch (currentEvent) {
            case 'agents':
              onAgents(JSON.parse(raw) as SystemHealthPayload);
              break;
            case 'token':
              onToken((JSON.parse(raw) as { text: string }).text);
              break;
            case 'done':
              onDone(JSON.parse(raw) as StreamDonePayload);
              break;
            case 'error':
              onError((JSON.parse(raw) as { detail: string }).detail);
              break;
          }
          currentEvent = '';
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

async function _fallback(
  message: string,
  history: { role: string; content: string }[],
  token: string | undefined,
  onAgents: (payload: SystemHealthPayload) => void,
  onToken: (text: string) => void,
  onDone: (payload: StreamDonePayload) => void,
  onError: (detail: string) => void
): Promise<void> {
  try {
    const result = await fetchCheckin(message, history, token);
    onAgents(result);
    if (result.liaison_feedback) {
      onToken(result.liaison_feedback);
    }
    onDone({
      responding_agent: result.responding_agent ?? 'liaison',
      contact_pauses: [],
      task_completions: [],
      active_pauses: result.active_pauses,
      behavioral_profiles: result.behavioral_profiles,
      behavioral_summary: result.behavioral_summary,
    });
  } catch (err) {
    onError(err instanceof Error ? err.message : 'Failed to connect.');
  }
}
