import { AuthUser, SystemHealthPayload } from '../types';

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
