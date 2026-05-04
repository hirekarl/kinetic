import { useId } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import { version } from '../../package.json';

interface LogoProps {
  size?: number;
}

/**
 * Inline SVG logo sub-component — three converging lines forming the letter K,
 * with an emerald glow applied to the central node.
 */
function KineticLogo({ size = 32 }: LogoProps) {
  const id = useId();
  const filterId = `kinetic-glow-${id}`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <circle cx="20" cy="20" r="20" fill="#09090b" />
      <defs>
        <filter id={filterId} x="-80%" y="-80%" width="260%" height="260%">
          <feGaussianBlur stdDeviation="2" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <line
        x1="10"
        y1="8"
        x2="20"
        y2="20"
        stroke="#10b981"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <line
        x1="10"
        y1="32"
        x2="20"
        y2="20"
        stroke="#10b981"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <line
        x1="31"
        y1="13"
        x2="20"
        y2="20"
        stroke="#10b981"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <circle cx="20" cy="20" r="2.5" fill="#10b981" filter={`url(#${filterId})`} />
    </svg>
  );
}

const DOMAINS = [
  {
    name: 'Bio Archivist',
    tagline: 'Bio-Metric Intelligence',
    borderClass: 'border-emerald-500/30 hover:border-emerald-500/60',
    accentClass: 'text-emerald-500',
    dotClass: 'bg-emerald-500',
    description:
      'Sleep debt, burnout index, nutrition signals. Know your operational ceiling before you hit it.',
  },
  {
    name: 'Logistics Fixer',
    tagline: 'Task Triage Engine',
    borderClass: 'border-amber-500/30 hover:border-amber-500/60',
    accentClass: 'text-amber-500',
    dotClass: 'bg-amber-500',
    description:
      'Task triage, outsourcing ROI, time recovery. Every item has a cost — Kinetic calculates it.',
  },
  {
    name: 'Relational Diplomat',
    tagline: 'Connection Margin Monitor',
    borderClass: 'border-blue-500/30 hover:border-blue-500/60',
    accentClass: 'text-blue-400',
    dotClass: 'bg-blue-400',
    description:
      'Connection margin, interaction sprints, drift alerts. Relationships decay on a schedule — stay ahead of it.',
  },
] as const;

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'One message',
    description: 'Type a free-text check-in. Plain language, no forms, no structure required.',
  },
  {
    step: '02',
    title: 'AI triage',
    description:
      'Parsed by Gemini 2.5 Flash across three domains simultaneously. Sub-second analysis.',
  },
  {
    step: '03',
    title: 'Prioritized action',
    description:
      'A single ranked feed of what to do next — across bio, logistics, and relational domains.',
  },
] as const;

/**
 * Marketing landing page rendered at `/` for unauthenticated visitors.
 *
 * Includes the sticky nav, hero section, the three agent domain cards, the
 * "How It Works" steps, and a footer. All sections are static — no props needed.
 */
export function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans">
      <Helmet>
        <title>Kinetic — Bio-Operational Triage Engine</title>
        <meta
          name="description"
          content="Personal infrastructure for high-performance engineers. AI triage across biology, logistics, and relationships — one prioritized action feed, seconds after check-in."
        />
      </Helmet>
      <nav className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="flex items-center gap-3">
            <KineticLogo size={32} />
            <span className="text-sm font-bold tracking-[0.2em] uppercase text-zinc-100">
              Kinetic
            </span>
          </Link>
          <Link
            to="/login"
            className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-950 transition-opacity hover:opacity-90"
          >
            Sign In
          </Link>
        </div>
      </nav>

      <section className="mx-auto max-w-4xl px-6 pb-20 pt-24 text-center">
        <p className="mb-6 font-mono text-xs uppercase tracking-widest text-emerald-500">
          {`[SYSTEM v${version}]`}
        </p>
        <h1 className="mb-6 text-5xl font-bold leading-tight tracking-tight text-white md:text-6xl">
          Your infrastructure
          <br />
          is showing.
        </h1>
        <p className="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-zinc-400">
          Kinetic monitors your biology, time, and relationships — and surfaces what to act on,
          right now.
        </p>
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link
            to="/login"
            className="rounded-lg bg-zinc-100 px-6 py-3 text-sm font-semibold text-zinc-950 shadow-[0_0_24px_rgba(16,185,129,0.12)] transition-opacity hover:opacity-90"
          >
            Access Mission Control →
          </Link>
        </div>
        <div className="mt-8 flex items-center justify-center gap-2">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
          <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-500">
            3 triage items · 2 domains active
          </span>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <p className="mb-10 text-center font-mono text-xs uppercase tracking-widest text-zinc-500">
          — Agent Architecture —
        </p>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          {DOMAINS.map((domain) => (
            <div
              key={domain.name}
              className={`rounded-xl border bg-zinc-900 p-6 transition-all duration-200 ${domain.borderClass}`}
            >
              <div className="mb-4 flex items-center gap-3">
                <span className={`h-2 w-2 rounded-full ${domain.dotClass}`} />
                <span
                  className={`font-mono text-[10px] uppercase tracking-widest ${domain.accentClass}`}
                >
                  {domain.tagline}
                </span>
              </div>
              <h3 className="mb-3 text-base font-semibold text-zinc-100">{domain.name}</h3>
              <p className="text-sm leading-relaxed text-zinc-400">{domain.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-zinc-800 bg-zinc-900/30">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <p className="mb-12 text-center font-mono text-xs uppercase tracking-widest text-zinc-500">
            — Operational Protocol —
          </p>
          <div className="grid grid-cols-1 gap-10 md:grid-cols-3">
            {HOW_IT_WORKS.map((item) => (
              <div key={item.step}>
                <div className="mb-5 flex items-center gap-4">
                  <span className="font-mono text-3xl font-bold text-zinc-700">{item.step}</span>
                  <div className="h-px flex-1 bg-zinc-800 md:hidden" />
                </div>
                <h3 className="mb-2 text-base font-semibold text-zinc-100">{item.title}</h3>
                <p className="text-sm leading-relaxed text-zinc-400">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-zinc-800 bg-zinc-950">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <div className="flex items-center gap-3">
            <KineticLogo size={24} />
            <div>
              <span className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-300">
                Kinetic
              </span>
              <p className="mt-0.5 text-[10px] text-zinc-600">Bio-Operational Triage Engine</p>
            </div>
          </div>
          <Link
            to="/login"
            className="font-mono text-xs uppercase tracking-wider text-zinc-400 transition-colors hover:text-zinc-200"
          >
            Sign In →
          </Link>
        </div>
      </footer>
    </div>
  );
}
