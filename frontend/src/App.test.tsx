import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App — split-panel shell', () => {
  it('renders the chat panel', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /brief kinetic/i })).toBeInTheDocument();
  });

  it('renders the dashboard panel', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /mission control/i })).toBeInTheDocument();
  });

  it('renders the initial idle state', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /system idle/i })).toBeInTheDocument();
  });
});
