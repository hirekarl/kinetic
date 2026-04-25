import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App — split-panel shell', () => {
  it('renders the chat panel', () => {
    render(<App />);
    expect(screen.getByRole('region', { name: /chat panel/i })).toBeInTheDocument();
  });

  it('renders the dashboard panel', () => {
    render(<App />);
    expect(screen.getByRole('region', { name: /dashboard panel/i })).toBeInTheDocument();
  });

  it('renders the Kinetic heading', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: /kinetic/i })).toBeInTheDocument();
  });
});
