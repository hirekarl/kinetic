import { render, screen, fireEvent, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { OnboardingModal } from './OnboardingModal';

describe('OnboardingModal', () => {
  const onClose = vi.fn();

  beforeEach(() => {
    onClose.mockReset();
  });

  it('renders step 0 heading — "Personal Infrastructure"', () => {
    render(<OnboardingModal onClose={onClose} />);
    expect(screen.getByRole('heading', { name: /personal infrastructure/i })).toBeInTheDocument();
  });

  it('has role="dialog" and aria-modal="true"', () => {
    render(<OnboardingModal onClose={onClose} />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('dialog is labelled by the heading', () => {
    render(<OnboardingModal onClose={onClose} />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-labelledby', 'onboarding-title');
    expect(document.getElementById('onboarding-title')).toBeInTheDocument();
  });

  it('step indicator labels step 0 as "Step 1 of 3"', () => {
    render(<OnboardingModal onClose={onClose} />);
    expect(screen.getByLabelText(/step 1 of 3/i)).toBeInTheDocument();
  });

  it('Back button is absent on step 0', () => {
    render(<OnboardingModal onClose={onClose} />);
    expect(screen.queryByRole('button', { name: /back/i })).not.toBeInTheDocument();
  });

  it('Next advances to step 1 — "Chat-First"', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByRole('heading', { name: /chat-first/i })).toBeInTheDocument();
  });

  it('Next again advances to step 2 — "Your Agent Team"', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByRole('heading', { name: /your agent team/i })).toBeInTheDocument();
  });

  it('step indicator reads "Step 2 of 3" on step 1', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByLabelText(/step 2 of 3/i)).toBeInTheDocument();
  });

  it('step indicator reads "Step 3 of 3" on step 2', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByLabelText(/step 3 of 3/i)).toBeInTheDocument();
  });

  it('Back on step 2 returns to step 1', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.click(screen.getByRole('button', { name: /back/i }));
    expect(screen.getByRole('heading', { name: /chat-first/i })).toBeInTheDocument();
  });

  it('Skip calls onClose from step 0', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /skip/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('Skip calls onClose from step 1', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.click(screen.getByRole('button', { name: /skip/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('Skip is absent on step 2', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.queryByRole('button', { name: /skip/i })).not.toBeInTheDocument();
  });

  it('Done on step 2 calls onClose', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.click(screen.getByRole('button', { name: /done/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('Done is absent on steps 0 and 1', () => {
    render(<OnboardingModal onClose={onClose} />);
    expect(screen.queryByRole('button', { name: /done/i })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.queryByRole('button', { name: /done/i })).not.toBeInTheDocument();
  });

  it('Escape key calls onClose', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('clicking the backdrop button calls onClose', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /close onboarding/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('clicking inside the dialog does not call onClose', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('dialog'));
    expect(onClose).not.toHaveBeenCalled();
  });

  it('Tab on last focusable element wraps focus to first element', () => {
    render(<OnboardingModal onClose={onClose} />);
    const dialog = screen.getByRole('dialog');
    const buttons = within(dialog).getAllByRole('button');
    const last = buttons[buttons.length - 1]!;
    last.focus();
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: false });
    expect(document.activeElement).toBe(buttons[0]);
  });

  it('Shift+Tab on first focusable element wraps focus to last element', () => {
    render(<OnboardingModal onClose={onClose} />);
    const dialog = screen.getByRole('dialog');
    const buttons = within(dialog).getAllByRole('button');
    buttons[0]!.focus();
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(buttons[buttons.length - 1]);
  });

  it('Tab handler is a no-op when the dialog has no focusable children', () => {
    render(<OnboardingModal onClose={onClose} />);
    const dialog = screen.getByRole('dialog');
    within(dialog)
      .getAllByRole('button')
      .forEach((b) => { b.remove(); });
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(onClose).not.toHaveBeenCalled();
  });

  it('step 2 shows all three agent names', () => {
    render(<OnboardingModal onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    fireEvent.click(screen.getByRole('button', { name: /next/i }));
    expect(screen.getByText(/bio-metric archivist/i)).toBeInTheDocument();
    expect(screen.getByText(/logistics fixer/i)).toBeInTheDocument();
    expect(screen.getByText(/relational diplomat/i)).toBeInTheDocument();
  });
});
