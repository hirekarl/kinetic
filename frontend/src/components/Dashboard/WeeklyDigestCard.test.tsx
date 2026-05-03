import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { WeeklyDigestCard } from './WeeklyDigestCard';
import type { DigestResponse } from '../../types';

function digestWithOffset(offsetMs: number): DigestResponse {
  return {
    summary: 'You had a solid 14 days. Sleep averaged 7.2 hours with slight improvement.',
    generated_at: new Date(Date.now() - offsetMs).toISOString(),
  };
}

const mockDigest = digestWithOffset(5 * 60 * 1000); // ~5 min ago

const errorDigest: DigestResponse = {
  summary: '[DIGEST ERROR] Gemini API is unavailable.',
  generated_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
};

describe('WeeklyDigestCard', () => {
  it('renders loading skeleton when isLoading is true', () => {
    render(<WeeklyDigestCard digest={null} isLoading={true} />);
    expect(screen.getByLabelText(/loading weekly digest/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /weekly review/i })).not.toBeInTheDocument();
  });

  it('renders "Weekly Review" trigger button when not loading', () => {
    render(<WeeklyDigestCard digest={null} />);
    expect(screen.getByRole('button', { name: /weekly review/i })).toBeInTheDocument();
  });

  it('is collapsed by default (aria-expanded=false)', () => {
    render(<WeeklyDigestCard digest={mockDigest} />);
    expect(screen.getByRole('button', { name: /weekly review/i })).toHaveAttribute(
      'aria-expanded',
      'false'
    );
  });

  it('does not show summary content when collapsed', () => {
    render(<WeeklyDigestCard digest={mockDigest} />);
    expect(screen.queryByText(/solid 14 days/i)).not.toBeInTheDocument();
  });

  it('expands on click and sets aria-expanded to true', async () => {
    const user = userEvent.setup();
    render(<WeeklyDigestCard digest={mockDigest} />);
    const trigger = screen.getByRole('button', { name: /weekly review/i });
    await user.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'true');
  });

  it('shows summary text when expanded', async () => {
    const user = userEvent.setup();
    render(<WeeklyDigestCard digest={mockDigest} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.getByText(/solid 14 days/i)).toBeInTheDocument();
  });

  it('shows relative timestamp ("X minutes ago") when expanded', async () => {
    const user = userEvent.setup();
    const digest = digestWithOffset(5 * 60 * 1000);
    render(<WeeklyDigestCard digest={digest} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.getByText(/minutes ago/i)).toBeInTheDocument();
  });

  it('shows "1 hour ago" (singular) when generated ~61 min ago', async () => {
    const user = userEvent.setup();
    const digest = digestWithOffset(61 * 60 * 1000);
    render(<WeeklyDigestCard digest={digest} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.getByText(/1 hour ago/i)).toBeInTheDocument();
  });

  it('shows "just now" when generated less than 1 minute ago', async () => {
    const user = userEvent.setup();
    const digest = digestWithOffset(30 * 1000); // 30 seconds ago
    render(<WeeklyDigestCard digest={digest} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.getByText(/just now/i)).toBeInTheDocument();
  });

  it('shows "2 hours ago" (plural) when generated 2+ hours ago', async () => {
    const user = userEvent.setup();
    const digest = digestWithOffset(130 * 60 * 1000); // 130 minutes = 2 hours
    render(<WeeklyDigestCard digest={digest} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.getByText(/2 hours ago/i)).toBeInTheDocument();
  });

  it('shows "1 minute ago" (singular) when generated exactly 1 minute ago', async () => {
    const user = userEvent.setup();
    const digest = digestWithOffset(60 * 1000); // exactly 1 minute ago
    render(<WeeklyDigestCard digest={digest} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.getByText(/1 minute ago/i)).toBeInTheDocument();
  });

  it('shows no-data message when digest is null and expanded', async () => {
    const user = userEvent.setup();
    render(<WeeklyDigestCard digest={null} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.getByText(/no check-in data yet/i)).toBeInTheDocument();
  });

  it('shows error block when summary starts with [DIGEST ERROR]', async () => {
    const user = userEvent.setup();
    render(<WeeklyDigestCard digest={errorDigest} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.getByText(/gemini api is unavailable/i)).toBeInTheDocument();
  });

  it('shows Refresh button when expanded and onRefresh is provided', async () => {
    const user = userEvent.setup();
    render(<WeeklyDigestCard digest={mockDigest} onRefresh={vi.fn()} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.getByRole('button', { name: /^refresh$/i })).toBeInTheDocument();
  });

  it('calls onRefresh when Refresh button is clicked', async () => {
    const mockRefresh = vi.fn();
    const user = userEvent.setup();
    render(<WeeklyDigestCard digest={mockDigest} onRefresh={mockRefresh} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    await user.click(screen.getByRole('button', { name: /^refresh$/i }));
    expect(mockRefresh).toHaveBeenCalledOnce();
  });

  it('shows spinner on Refresh button when isRefreshing is true', async () => {
    const user = userEvent.setup();
    render(<WeeklyDigestCard digest={mockDigest} onRefresh={vi.fn()} isRefreshing={true} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.getByRole('button', { name: /refreshing/i })).toBeInTheDocument();
  });

  it('collapses on second click', async () => {
    const user = userEvent.setup();
    render(<WeeklyDigestCard digest={mockDigest} />);
    const trigger = screen.getByRole('button', { name: /weekly review/i });
    await user.click(trigger);
    await user.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText(/solid 14 days/i)).not.toBeInTheDocument();
  });

  it('does not show Refresh button when onRefresh is not provided', async () => {
    const user = userEvent.setup();
    render(<WeeklyDigestCard digest={mockDigest} />);
    await user.click(screen.getByRole('button', { name: /weekly review/i }));
    expect(screen.queryByRole('button', { name: /refresh/i })).not.toBeInTheDocument();
  });
});
