import { useState, useEffect } from 'react';
import { ChatPanel, Message } from './components/ChatPanel';
import { BioStatusCard } from './components/Dashboard/BioStatusCard';
import { LogisticsStatusCard } from './components/Dashboard/LogisticsStatusCard';
import { RelationalStatusCard } from './components/Dashboard/RelationalStatusCard';
import { TriageList } from './components/Dashboard/TriageList';
import { ROISummaryCard } from './components/Dashboard/ROISummaryCard';
import { BehavioralProfilePanel } from './components/Dashboard/BehavioralProfilePanel';
import { StatusBadge } from './components/Dashboard/StatusBadge';
import { fetchCheckin, fetchHistory } from './api/client';
import { SystemHealthPayload } from './types';

function App() {
  const [health, setHealth] = useState<SystemHealthPayload | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Hydrate state from backend on mount
  useEffect(() => {
    setIsLoading(true);
    void fetchHistory()
      .then((data) => {
        setHealth(data.health);
        setMessages(data.messages);
      })
      .catch((err: unknown) => {
        console.error('Failed to hydrate state', err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const handleSendMessage = (content: string) => {
    // 1. Add user message to feed immediately
    const userMsg: Message = { role: 'user', content };
    setMessages((prev) => [...prev, userMsg]);

    setIsLoading(true);
    setError(null);

    void fetchCheckin(content, messages)
      .then((result) => {
        setHealth(result);
        // 2. Add liaison feedback to feed
        if (result.liaison_feedback) {
          const systemMsg: Message = { role: 'system', content: result.liaison_feedback };
          setMessages((prev) => [...prev, systemMsg]);
        }
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : 'Failed to update system health.';
        setError(msg);
        setMessages((prev) => [...prev, { role: 'system', content: `[CRITICAL ERROR] ${msg}` }]);
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to wipe all system data? This cannot be undone.')) return;

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}/api/debug/reset`,
        {
          method: 'POST',
        }
      );
      if (response.ok) {
        setHealth(null);
        setMessages([]);
        setError(null);
      }
    } catch (err) {
      console.error('Reset failed', err);
    }
  };

  return (
    <div className="flex h-screen w-full bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
      {/* Left Panel: Operational Liaison Feed */}
      <div className="w-[420px] shrink-0">
        <ChatPanel onSendMessage={handleSendMessage} isLoading={isLoading} messages={messages} />
      </div>

      {/* Right Panel: Mission Control Dashboard */}
      <main className="flex-1 flex flex-col min-w-0 bg-zinc-900/30">
        {/* Top Header */}
        <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950 px-8 py-4">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-bold tracking-tight text-white">Mission Control</h2>
            {health && <StatusBadge status={health.overall_status} />}
          </div>

          <div className="flex items-center gap-6">
            <button
              onClick={() => {
                void handleReset();
              }}
              className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:text-rose-500 transition-colors"
            >
              Reset System
            </button>
            <div className="text-[10px] font-mono text-zinc-400 uppercase">
              System Time: {new Date().toLocaleTimeString()}
            </div>
          </div>
        </header>

        {/* Scrollable Content */}
        {/* tabIndex={0} is required to satisfy axe scrollable-region-focusable on content-only regions */}
        {/* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex */}
        <div className="flex-1 overflow-y-auto p-8" tabIndex={0}>
          {error && (
            <div className="mb-8 rounded-lg border border-status-red/20 bg-status-red/5 p-4 text-sm text-status-red">
              <span className="font-bold">SYSTEM ERROR:</span> {error}
            </div>
          )}

          {!health && !isLoading && !error && (
            <div className="flex h-[60vh] flex-col items-center justify-center text-center">
              <div className="mb-4 h-12 w-12 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center">
                <div className="h-2 w-2 rounded-full bg-zinc-700 animate-pulse" />
              </div>
              <h3 className="text-lg font-medium text-zinc-100">System Idle</h3>
              <p className="max-w-xs text-sm text-zinc-400 mt-2 leading-relaxed">
                Brief Kinetic via the panel to the left to begin personal infrastructure triage.
              </p>
            </div>
          )}

          {health && (
            <div className="mx-auto max-w-5xl space-y-12">
              {/* Status Grid */}
              <section>
                <div className="mb-4 text-xs font-semibold uppercase tracking-widest text-zinc-400">
                  Sector Status
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <BioStatusCard data={health.bio} isLoading={isLoading} />
                  <LogisticsStatusCard data={health.logistics} isLoading={isLoading} />
                  <RelationalStatusCard data={health.relational} isLoading={isLoading} />
                </div>
              </section>

              {/* Triage Section */}
              <section>
                <TriageList items={health.triage_items} isLoading={isLoading} />
              </section>

              {/* ROI Section */}
              {health.roi_summary && (
                <section>
                  <ROISummaryCard data={health.roi_summary} isLoading={isLoading} />
                </section>
              )}

              {/* Behavioral Profile Section */}
              <section>
                <BehavioralProfilePanel
                  profiles={health.behavioral_profiles}
                  isLoading={isLoading}
                />
              </section>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
