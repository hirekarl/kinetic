import { SystemHealthPayload } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Fetches system health based on a natural-language check-in message.
 */
export async function fetchCheckin(
  message: string,
  history: { role: string; content: string }[] = []
): Promise<SystemHealthPayload> {
  const response = await fetch(`${API_BASE_URL}/api/checkin`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, history }),
  });

  if (!response.ok) {
    let errorMessage = 'An unexpected error occurred.';
    try {
      const errorData = (await response.json()) as { detail?: string };
      errorMessage = errorData.detail ?? errorMessage;
    } catch {
      // Fallback to status text
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  return response.json() as Promise<SystemHealthPayload>;
}

/**
 * Marks a logistics task as completed on the server.
 */
export async function completeTask(taskName: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/tasks/${encodeURIComponent(taskName)}/complete`,
    { method: 'PATCH' }
  );
  if (!response.ok) {
    throw new Error(`Failed to complete task '${taskName}': ${response.statusText}`);
  }
}

/**
 * Fetches the current system health and message history.
 */
export async function fetchHistory(): Promise<{
  health: SystemHealthPayload;
  messages: { role: 'user' | 'system'; content: string }[];
}> {
  const response = await fetch(`${API_BASE_URL}/api/history`);

  if (!response.ok) {
    throw new Error('Failed to fetch system history.');
  }

  return response.json() as Promise<{
    health: SystemHealthPayload;
    messages: { role: 'user' | 'system'; content: string }[];
  }>;
}
