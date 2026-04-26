import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StatusBadge } from './StatusBadge';

describe('StatusBadge', () => {
  it('renders "Healthy" label for green status', () => {
    render(<StatusBadge status="green" />);
    expect(screen.getByText('Healthy')).toBeInTheDocument();
  });

  it('renders "Degraded" label for yellow status', () => {
    render(<StatusBadge status="yellow" />);
    expect(screen.getByText('Degraded')).toBeInTheDocument();
  });

  it('renders "Critical" label for red status', () => {
    render(<StatusBadge status="red" />);
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  it('renders custom label when provided', () => {
    render(<StatusBadge status="green" label="All Clear" />);
    expect(screen.getByText('All Clear')).toBeInTheDocument();
  });
});
