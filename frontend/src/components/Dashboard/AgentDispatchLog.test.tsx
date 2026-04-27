import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { AgentDispatchLog } from './AgentDispatchLog';
import type { AgentLogEntry } from '../../types';

const MOCK_ENTRY: AgentLogEntry = {
  id: 'entry-1',
  timestamp: '2026-04-26T10:30:00.000Z',
  user_message: 'Slept 5 hours, feeling okay',
  agents_fired: [
    {
      domain: 'bio',
      status: 'yellow',
      summary: 'Burnout 65/100 · Moderate risk at current trajectory',
    },
    { domain: 'logistics', status: 'green', summary: '0 critical · 0min to resolve' },
  ],
  responding_agent: 'bio_archivist',
  overall_status: 'yellow',
};

const LONG_MESSAGE_ENTRY: AgentLogEntry = {
  ...MOCK_ENTRY,
  id: 'entry-long',
  user_message:
    'This is a very long user message that exceeds sixty characters easily in this test',
};

describe('AgentDispatchLog', () => {
  it('renders the panel trigger button', () => {
    render(<AgentDispatchLog entries={[]} />);
    expect(screen.getByRole('button', { name: /agent dispatch log/i })).toBeInTheDocument();
  });

  it('is collapsed by default (aria-expanded false on panel trigger)', () => {
    render(<AgentDispatchLog entries={[]} />);
    expect(screen.getByRole('button', { name: /agent dispatch log/i })).toHaveAttribute(
      'aria-expanded',
      'false'
    );
  });

  it('shows empty state after expanding panel when entries is empty', async () => {
    const user = userEvent.setup();
    render(<AgentDispatchLog entries={[]} />);
    await user.click(screen.getByRole('button', { name: /agent dispatch log/i }));
    expect(screen.getByText(/no check-ins yet this session/i)).toBeInTheDocument();
  });

  it('shows entry count badge when entries exist', () => {
    render(<AgentDispatchLog entries={[MOCK_ENTRY]} />);
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('does not show entry content when panel is collapsed', () => {
    render(<AgentDispatchLog entries={[MOCK_ENTRY]} />);
    expect(screen.queryByText(/slept 5 hours/i)).not.toBeInTheDocument();
  });

  it('shows entry row content after expanding panel', async () => {
    const user = userEvent.setup();
    render(<AgentDispatchLog entries={[MOCK_ENTRY]} />);
    await user.click(screen.getByRole('button', { name: /agent dispatch log/i }));
    expect(screen.getByText(/slept 5 hours/i)).toBeInTheDocument();
  });

  it('hides agent summaries before entry is expanded', async () => {
    const user = userEvent.setup();
    render(<AgentDispatchLog entries={[MOCK_ENTRY]} />);
    await user.click(screen.getByRole('button', { name: /agent dispatch log/i }));
    expect(screen.queryByText(/burnout 65\/100/i)).not.toBeInTheDocument();
  });

  it('shows agent summaries after expanding an entry', async () => {
    const user = userEvent.setup();
    render(<AgentDispatchLog entries={[MOCK_ENTRY]} />);
    await user.click(screen.getByRole('button', { name: /agent dispatch log/i }));
    const entryBtn = screen.getByRole('button', { name: /slept 5 hours/i });
    await user.click(entryBtn);
    expect(screen.getByText(/burnout 65\/100/i)).toBeInTheDocument();
    expect(screen.getByText(/0 critical/i)).toBeInTheDocument();
  });

  it('collapses entry again on second click', async () => {
    const user = userEvent.setup();
    render(<AgentDispatchLog entries={[MOCK_ENTRY]} />);
    await user.click(screen.getByRole('button', { name: /agent dispatch log/i }));
    const entryBtn = screen.getByRole('button', { name: /slept 5 hours/i });
    await user.click(entryBtn);
    await user.click(entryBtn);
    expect(screen.queryByText(/burnout 65\/100/i)).not.toBeInTheDocument();
  });

  it('renders domain chips for fired agents only', async () => {
    const user = userEvent.setup();
    render(<AgentDispatchLog entries={[MOCK_ENTRY]} />);
    await user.click(screen.getByRole('button', { name: /agent dispatch log/i }));
    expect(screen.getByText('BIO')).toBeInTheDocument();
    expect(screen.getByText('LOGISTICS')).toBeInTheDocument();
    expect(screen.queryByText('RELATIONAL')).not.toBeInTheDocument();
  });

  it('renders responding_agent badge when present', async () => {
    const user = userEvent.setup();
    render(<AgentDispatchLog entries={[MOCK_ENTRY]} />);
    await user.click(screen.getByRole('button', { name: /agent dispatch log/i }));
    expect(screen.getByText(/bio_archivist/i)).toBeInTheDocument();
  });

  it('does not render responding_agent badge when null', async () => {
    const user = userEvent.setup();
    const noAgentEntry: AgentLogEntry = { ...MOCK_ENTRY, id: 'no-agent', responding_agent: null };
    render(<AgentDispatchLog entries={[noAgentEntry]} />);
    await user.click(screen.getByRole('button', { name: /agent dispatch log/i }));
    expect(screen.queryByText(/bio_archivist/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/→/)).not.toBeInTheDocument();
  });

  it('renders loading skeleton (no panel trigger) when isLoading is true', () => {
    render(<AgentDispatchLog entries={[]} isLoading={true} />);
    expect(screen.queryByRole('button', { name: /agent dispatch log/i })).not.toBeInTheDocument();
  });

  it('truncates user message to 60 chars with ellipsis', async () => {
    const user = userEvent.setup();
    render(<AgentDispatchLog entries={[LONG_MESSAGE_ENTRY]} />);
    await user.click(screen.getByRole('button', { name: /agent dispatch log/i }));
    expect(screen.queryByText(LONG_MESSAGE_ENTRY.user_message)).not.toBeInTheDocument();
    expect(screen.getByText(/…/)).toBeInTheDocument();
  });
});
