import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { LoginScreen } from './LoginScreen';

describe('LoginScreen', () => {
  const mockOnLogin = vi.fn().mockResolvedValue(undefined);

  const renderScreen = (overrides?: { error?: string | null; isLoading?: boolean }) =>
    render(
      <MemoryRouter>
        <LoginScreen onLogin={mockOnLogin} error={null} isLoading={false} {...overrides} />
      </MemoryRouter>
    );

  it('renders the Kinetic heading and subtitle', () => {
    renderScreen();
    expect(screen.getByRole('heading', { name: /^kinetic$/i })).toBeInTheDocument();
    expect(
      screen.getByText(/personal infrastructure for high-performance engineers/i)
    ).toBeInTheDocument();
  });

  it('renders a labelled username input and a labelled password input', () => {
    renderScreen();
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('submit button shows "Signing in…" and is disabled while isLoading=true', () => {
    renderScreen({ isLoading: true });
    const btn = screen.getByRole('button', { name: /signing in/i });
    expect(btn).toBeDisabled();
  });

  it('submit button shows "Sign in" and is enabled while isLoading=false', () => {
    renderScreen();
    expect(screen.getByRole('button', { name: /^sign in$/i })).toBeEnabled();
  });

  it('error message renders with role="alert" when error prop is set', () => {
    renderScreen({ error: 'Invalid credentials' });
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Invalid credentials');
  });

  it('error alert is absent when error is null', () => {
    renderScreen();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('form submission calls onLogin with entered username and password', async () => {
    const user = userEvent.setup();
    renderScreen();
    await user.type(screen.getByLabelText(/username/i), 'demo');
    await user.type(screen.getByLabelText(/password/i), 'secret');
    await user.click(screen.getByRole('button', { name: /^sign in$/i }));
    expect(mockOnLogin).toHaveBeenCalledWith('demo', 'secret');
  });

  it('inputs have proper HTML labels, not just placeholders', () => {
    renderScreen();
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    expect(usernameInput.tagName).toBe('INPUT');
    expect(passwordInput.tagName).toBe('INPUT');
    expect(usernameInput).toHaveAttribute('type', 'text');
    expect(passwordInput).toHaveAttribute('type', 'password');
  });
});
