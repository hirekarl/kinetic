import { useState } from 'react';
import { ChatPanel } from './components/ChatPanel';
import { BioStatusCard } from './components/Dashboard/BioStatusCard';
import { LogisticsStatusCard } from './components/Dashboard/LogisticsStatusCard';
import { RelationalStatusCard } from './components/Dashboard/RelationalStatusCard';
import { TriageList } from './components/Dashboard/TriageList';
import { ROISummaryCard } from './components/Dashboard/ROISummaryCard';
import { StatusBadge } from './components/Dashboard/StatusBadge';

import { fetchCheckin } from './api/client';
import { SystemHealthPayload } from './types';

function App() {
  const [health, setHealth] = useState<SystemHealthPayload | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendMessage = (message: string) => {
    setIsLoading(true);
    setError(null);
    void fetchCheckin(message)
      .then((result) => {
        setHealth(result);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to update system health.');
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  return (
    <div className="flex h-screen w-full bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
      {/* Left Panel: Chat */}
      <div className="w-[380px] shrink-0">
        <ChatPanel onSendMessage={handleSendMessage} isLoading={isLoading} />
      </div>

      {/* Right Panel: Dashboard */}
      <main className="flex-1 flex flex-col min-w-0 bg-zinc-900/30">
        {/* Top Header */}
        <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950 px-8 py-4">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-bold tracking-tight text-white">Mission Control</h2>
            {health && <StatusBadge status={health.overall_status} />}
          </div>
          <div className="text-[10px] font-mono text-zinc-500 uppercase">
            System Time: {new Date().toLocaleTimeString()}
          </div>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-8">
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
              <p className="max-w-xs text-sm text-zinc-500 mt-2 leading-relaxed">
                Brief Kinetic via the panel to the left to begin personal infrastructure triage.
              </p>
            </div>
          )}

          {health && (
            <div className="mx-auto max-w-5xl space-y-12">
              {/* Status Grid */}
              <section>
                <div className="mb-4 text-xs font-semibold uppercase tracking-widest text-zinc-500">
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
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
