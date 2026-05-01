import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { LandingPage } from './LandingPage';

const renderLanding = () =>
  render(
    <MemoryRouter>
      <LandingPage />
    </MemoryRouter>
  );

describe('LandingPage', () => {
  it('renders the hero heading', () => {
    renderLanding();
    expect(
      screen.getByRole('heading', { name: /your infrastructure is showing/i })
    ).toBeInTheDocument();
  });

  it('renders "Access Mission Control" CTA as a link to /login', () => {
    renderLanding();
    const cta = screen.getByRole('link', { name: /access mission control/i });
    expect(cta).toBeInTheDocument();
    expect(cta).toHaveAttribute('href', '/login');
  });

  it('renders three domain cards — Bio Archivist, Logistics Fixer, Relational Diplomat', () => {
    renderLanding();
    expect(screen.getByText(/bio archivist/i)).toBeInTheDocument();
    expect(screen.getByText(/logistics fixer/i)).toBeInTheDocument();
    expect(screen.getByText(/relational diplomat/i)).toBeInTheDocument();
  });

  it('renders a nav Sign In link pointing to /login', () => {
    renderLanding();
    const signInLinks = screen.getAllByRole('link', { name: /sign in/i });
    expect(signInLinks.length).toBeGreaterThanOrEqual(1);
    expect(signInLinks[0]).toHaveAttribute('href', '/login');
  });

  it('renders footer brand text and a Sign In link', () => {
    renderLanding();
    expect(screen.getByText(/bio-operational triage engine/i)).toBeInTheDocument();
    const signInLinks = screen.getAllByRole('link', { name: /sign in/i });
    expect(signInLinks.length).toBeGreaterThanOrEqual(2);
  });

  it('renders the system version eyebrow', () => {
    renderLanding();
    expect(screen.getByText(/\[SYSTEM v1\.8\.0\]/i)).toBeInTheDocument();
  });

  it('renders all three how-it-works step titles', () => {
    renderLanding();
    expect(screen.getByText(/one message/i)).toBeInTheDocument();
    expect(screen.getByText(/ai triage/i)).toBeInTheDocument();
    expect(screen.getByText(/prioritized action/i)).toBeInTheDocument();
  });
});
