import type { FC } from 'react';

const App: FC = () => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        height: '100dvh',
        gap: '1px',
        background: 'var(--color-border)',
      }}
    >
      {/* Left panel: Chat input */}
      <section
        style={{
          background: 'var(--color-bg)',
          display: 'flex',
          flexDirection: 'column',
          padding: '1.5rem',
        }}
        aria-label="Chat panel"
      >
        <h1 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem' }}>Kinetic</h1>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
          Brief your system. What&apos;s your status?
        </p>
      </section>

      {/* Right panel: Dashboard */}
      <section
        style={{ background: 'var(--color-surface)', padding: '1.5rem' }}
        aria-label="Dashboard panel"
      >
        <p style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
          System health will appear here.
        </p>
      </section>
    </div>
  );
};

export default App;
