import { useState, useEffect } from 'react';
import { login as apiLogin, fetchMe, logout as apiLogout } from '../api/client';
import { AuthUser } from '../types';

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

  // Validate stored token on mount
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
