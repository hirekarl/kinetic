import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { BehavioralProfilePanel } from './BehavioralProfilePanel';
import { BehavioralProfile } from '../../types';

const mockProfiles: BehavioralProfile[] = [
  {
    profile_key: 'chronic_sleep_deficit',
    insight: 'Sleep consistently falls below 6 hours on weekdays.',
    evidence: { avg_weekday_sleep: 5.4, sample_days: 10 },
    first_observed: '2026-04-20T08:00:00',
    last_updated: '2026-04-25T08:00:00',
    observation_count: 5,
  },
  {
    profile_key: 'relational_drift_marcus',
    insight: 'Contact with Marcus has been declining over 2 weeks.',
    evidence: { drift_slope: 1.2 },
    first_observed: '2026-04-18T08:00:00',
    last_updated: '2026-04-24T08:00:00',
    observation_count: 3,
  },
];

describe('BehavioralProfilePanel', () => {
  it('renders the "Behavioral Profile" section heading', () => {
    render(<BehavioralProfilePanel profiles={[]} />);
    expect(screen.getByRole('button', { name: /behavioral profile/i })).toBeInTheDocument();
  });

  it('is collapsed by default (aria-expanded false)', () => {
    render(<BehavioralProfilePanel profiles={[]} />);
    expect(screen.getByRole('button', { name: /behavioral profile/i })).toHaveAttribute(
      'aria-expanded',
      'false'
    );
  });

  it('does not show content when collapsed', () => {
    render(<BehavioralProfilePanel profiles={mockProfiles} />);
    expect(
      screen.queryByText('Sleep consistently falls below 6 hours on weekdays.')
    ).not.toBeInTheDocument();
  });

  it('expands on click and sets aria-expanded to true', async () => {
    const user = userEvent.setup();
    render(<BehavioralProfilePanel profiles={mockProfiles} />);
    const trigger = screen.getByRole('button', { name: /behavioral profile/i });
    await user.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'true');
  });

  it('shows profile insights when expanded', async () => {
    const user = userEvent.setup();
    render(<BehavioralProfilePanel profiles={mockProfiles} />);
    await user.click(screen.getByRole('button', { name: /behavioral profile/i }));
    expect(
      screen.getByText('Sleep consistently falls below 6 hours on weekdays.')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Contact with Marcus has been declining over 2 weeks.')
    ).toBeInTheDocument();
  });

  it('shows profile_key labels when expanded', async () => {
    const user = userEvent.setup();
    render(<BehavioralProfilePanel profiles={mockProfiles} />);
    await user.click(screen.getByRole('button', { name: /behavioral profile/i }));
    expect(screen.getByText('chronic_sleep_deficit')).toBeInTheDocument();
    expect(screen.getByText('relational_drift_marcus')).toBeInTheDocument();
  });

  it('shows observation_count badge when expanded', async () => {
    const user = userEvent.setup();
    render(<BehavioralProfilePanel profiles={mockProfiles} />);
    await user.click(screen.getByRole('button', { name: /behavioral profile/i }));
    expect(screen.getByText('5 observations')).toBeInTheDocument();
    expect(screen.getByText('3 observations')).toBeInTheDocument();
  });

  it('collapses again on second click', async () => {
    const user = userEvent.setup();
    render(<BehavioralProfilePanel profiles={mockProfiles} />);
    const trigger = screen.getByRole('button', { name: /behavioral profile/i });
    await user.click(trigger);
    await user.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
    expect(
      screen.queryByText('Sleep consistently falls below 6 hours on weekdays.')
    ).not.toBeInTheDocument();
  });

  it('shows empty state message when profiles array is empty and expanded', async () => {
    const user = userEvent.setup();
    render(<BehavioralProfilePanel profiles={[]} />);
    await user.click(screen.getByRole('button', { name: /behavioral profile/i }));
    expect(screen.getByText(/building your profile/i)).toBeInTheDocument();
  });

  it('shows profile count in trigger when profiles exist', () => {
    render(<BehavioralProfilePanel profiles={mockProfiles} />);
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('shows loading skeleton and hides trigger content when isLoading is true', () => {
    render(<BehavioralProfilePanel profiles={[]} isLoading={true} />);
    expect(screen.queryByRole('button', { name: /behavioral profile/i })).not.toBeInTheDocument();
  });
});
