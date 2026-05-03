import { useState, useEffect } from 'react';
import { login as apiLogin, fetchMe, logout as apiLogout } from '../api/client';
import { AuthUser } from '../types';

/**
 * Manages authentication state for the current user.
 *
 * Persists the JWT to `localStorage` under `kinetic_token` so sessions survive
 * page refreshes. On mount, validates any stored token against `/api/auth/me`
 * and clears it if the token is expired or invalid — preventing a stale token
 * from reaching protected API calls.
 *
 * @returns An object with the authenticated user, the raw token string, a
 *   loading flag (true while the mount-time validation is in flight), and
 *   `login`/`logout` action callbacks.
 */
export function useAuth(): {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
} {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('kinetic_token'));
  const [isLoading, setIsLoading] = useState(() => !!localStorage.getItem('kinetic_token'));

  useEffect(() => {
    const storedToken = localStorage.getItem('kinetic_token');
    if (!storedToken) return;

    fetchMe(storedToken)
      .then((u) => {
        setUser(u);
      })
      .catch(() => {
        localStorage.removeItem('kinetic_token');
        setToken(null);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const login = async (username: string, password: string): Promise<void> => {
    const result = await apiLogin(username, password);
    localStorage.setItem('kinetic_token', result.access_token);
    setToken(result.access_token);
    const me = await fetchMe(result.access_token);
    setUser(me);
  };

  const logout = async (): Promise<void> => {
    if (token) {
      await apiLogout(token);
    }
    localStorage.removeItem('kinetic_token');
    setToken(null);
    setUser(null);
  };

  return { user, token, isLoading, login, logout };
}
