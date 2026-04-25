import { SystemHealthPayload } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Fetches system health based on a natural-language check-in message.
 */
export async function fetchCheckin(message: string): Promise<SystemHealthPayload> {
  const response = await fetch(`${API_BASE_URL}/api/checkin`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
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
