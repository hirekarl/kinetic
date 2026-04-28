import { AuthUser, DigestResponse, StreamDonePayload, SystemHealthPayload } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function authHeaders(token?: string): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

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

export async function completeTask(taskName: string, token?: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/tasks/${encodeURIComponent(taskName)}/complete`,
    { method: 'PATCH', headers: authHeaders(token) }
  );
  if (!response.ok) {
    throw new Error(`Failed to complete task '${taskName}': ${response.statusText}`);
  }
}

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

export async function fetchMe(token: string): Promise<AuthUser> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error('Not authenticated');
  }
  return response.json() as Promise<AuthUser>;
}

export async function logout(token: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/auth/logout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
}

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
