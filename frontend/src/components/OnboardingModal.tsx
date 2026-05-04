import React, { useState, useEffect, useRef } from 'react';

/** Props for the `OnboardingModal` component. */
interface OnboardingModalProps {
  /** Called when the user dismisses, skips, or completes all onboarding steps. */
  onClose: () => void;
}

const STEPS = [
  {
    heading: 'Personal Infrastructure',
    body: 'Most systems fail not from bad decisions but from unmanaged drift — sleep debt, task backlogs, fraying relationships. Kinetic tracks all three domains and surfaces one prioritized list.',
    agents: null as null | { name: string; role: string }[],
  },
  {
    heading: 'Chat-First',
    body: 'Just tell Kinetic how you\'re doing. Plain English is fine: "Slept 5 hours, haven\'t replied to Marcus in a week." It extracts what matters and routes it to the right agent.',
    agents: null,
  },
  {
    heading: 'Your Agent Team',
    body: null,
    agents: [
      { name: 'Bio-Metric Archivist', role: 'Sleep, nutrition, and burnout forecasting' },
      { name: 'Logistics Fixer', role: 'Task triage and outsourcing ROI' },
      { name: 'Relational Diplomat', role: 'Connection margin and interaction sprints' },
    ],
  },
];

const HEADING_ID = 'onboarding-title';

/**
 * Three-screen first-visit tutorial modal.
 *
 * Shown once per browser session; completion is persisted to `localStorage`
 * under `kinetic_onboarded` so it does not reappear after the user dismisses it.
 * Includes a focus trap (Tab/Shift-Tab cycle) and Escape-key dismiss for full
 * keyboard accessibility.
 */
export const OnboardingModal: React.FC<OnboardingModalProps> = ({ onClose }) => {
  const [step, setStep] = useState(0);
  const dialogRef = useRef<HTMLDivElement>(null);

  // Escape key dismiss
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [onClose]);

  // Focus trap — cycle Tab/Shift-Tab within the dialog panel
  useEffect(() => {
    const onTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab' || !dialogRef.current) return;
      const focusable = Array.from(
        dialogRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
      );
      if (!focusable.length) return;
      const first = focusable[0]!;
      const last = focusable[focusable.length - 1]!;
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener('keydown', onTab);
    return () => {
      document.removeEventListener('keydown', onTab);
    };
  }, []);

  // Move focus into the dialog on mount
  useEffect(() => {
    dialogRef.current?.focus();
  }, []);

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;
  const stepLabel = `Step ${String(step + 1)} of ${String(STEPS.length)}`;

  return (
    // Outer container: centers the dialog and provides the visual backdrop.
    // The actual backdrop click target is a sibling <button> behind the dialog
    // so click events never need to propagate through the dialog itself.
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop: mouse-only dismiss. tabIndex={-1} keeps it out of tab order;
          the focus trap + Escape key handle keyboard dismissal. */}
      <button
        type="button"
        aria-label="Close onboarding"
        tabIndex={-1}
        className="absolute inset-0 cursor-default bg-zinc-950/80"
        onClick={onClose}
      />

      {/* Dialog panel — sibling of backdrop, not child, so no stopPropagation needed */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={HEADING_ID}
        tabIndex={-1}
        className="relative z-10 w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-8 shadow-2xl outline-none"
      >
        {/* Step indicator */}
        <div role="group" aria-label={stepLabel} className="mb-6 flex justify-center gap-2">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1.5 w-6 rounded-full transition-colors ${
                i === step ? 'bg-zinc-200' : 'bg-zinc-700'
              }`}
            />
          ))}
        </div>

        {/* Heading */}
        <h2 id={HEADING_ID} className="mb-4 text-xl font-bold text-white">
          {current.heading}
        </h2>

        {/* Body copy */}
        {current.body && (
          <p className="mb-8 text-sm leading-relaxed text-zinc-400">{current.body}</p>
        )}

        {/* Agent list (step 2 only) */}
        {current.agents && (
          <ul className="mb-8 space-y-3">
            {current.agents.map((agent) => (
              <li
                key={agent.name}
                className="rounded-lg border border-zinc-800 bg-zinc-950 px-4 py-3"
              >
                <p className="text-sm font-semibold text-zinc-100">{agent.name}</p>
                <p className="text-xs text-zinc-400">{agent.role}</p>
              </li>
            ))}
          </ul>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <div>
            {step > 0 && (
              <button
                onClick={() => {
                  setStep((s) => s - 1);
                }}
                className="text-sm text-zinc-400 transition-colors hover:text-zinc-200"
              >
                Back
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            {!isLast && (
              <button
                onClick={onClose}
                className="text-sm text-zinc-400 transition-colors hover:text-zinc-200"
              >
                Skip
              </button>
            )}
            {isLast ? (
              <button
                onClick={onClose}
                className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 transition-colors hover:bg-white"
              >
                Done
              </button>
            ) : (
              <button
                onClick={() => {
                  setStep((s) => s + 1);
                }}
                className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 transition-colors hover:bg-white"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
