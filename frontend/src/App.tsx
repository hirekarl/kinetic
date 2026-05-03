import { useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { LandingPage } from './components/LandingPage';
import { ChatPanel } from './components/ChatPanel';
import { BioStatusCard } from './components/Dashboard/BioStatusCard';
import { LogisticsStatusCard } from './components/Dashboard/LogisticsStatusCard';
import { RelationalStatusCard } from './components/Dashboard/RelationalStatusCard';
import { TriageList } from './components/Dashboard/TriageList';
import { ROISummaryCard } from './components/Dashboard/ROISummaryCard';
import { BehavioralProfilePanel } from './components/Dashboard/BehavioralProfilePanel';
import { WeeklyDigestCard } from './components/Dashboard/WeeklyDigestCard';
import { AgentDispatchLog } from './components/Dashboard/AgentDispatchLog';
import { StatusBadge } from './components/Dashboard/StatusBadge';
import { OnboardingModal } from './components/OnboardingModal';
import { LoginScreen } from './components/LoginScreen';
import { simulateWeek, fetchHistory } from './api/client';
import { useAuth } from './hooks/useAuth';
import { useChat } from './hooks/useChat';
import { useDigest } from './hooks/useDigest';

function App() {
  const { user, token, isLoading: authLoading, login: authLogin, logout: authLogout } = useAuth();
  const navigate = useNavigate();
  const [loginError, setLoginError] = useState<string | null>(null);

  const {
    health,
    messages,
    agentLog,
    isLoading,
    error,
    lastMessage,
    streamingContent,
    handleSendMessage,
    handleRetry,
    handleCompleteTask,
    handleReset,
    setHealth,
    setMessages,
    clearSession,
  } = useChat(token);

  const { digestData, digestLoading, digestRefreshing, handleRefreshDigest, clearDigest } =
    useDigest(token);

  const [showOnboarding, setShowOnboarding] = useState(
    () => !localStorage.getItem('kinetic_onboarded')
  );
  const [isSimulating, setIsSimulating] = useState(false);

  const handleLogin = async (username: string, password: string) => {
    setLoginError(null);
    try {
      await authLogin(username, password);
      navigate('/app');
    } catch {
      setLoginError('Invalid credentials. Please try again.');
    }
  };

  const handleLogout = async () => {
    await authLogout();
    clearSession();
    clearDigest();
    navigate('/');
  };

  const handleSimulateWeek = async () => {
    if (!token) return;
    setIsSimulating(true);
    try {
      await simulateWeek(token);
      await handleRefreshDigest();
      const data = await fetchHistory(token);
      setHealth(data.health);
      setMessages(data.messages);
    } catch (err) {
      console.error('Simulation failed', err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleDismissOnboarding = () => {
    localStorage.setItem('kinetic_onboarded', 'true');
    setShowOnboarding(false);
  };

  if (authLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-zinc-950">
        <div className="h-3 w-3 rounded-full bg-zinc-700 animate-pulse" />
      </div>
    );
  }

  const dashboardElement = user ? (
    <div className="flex flex-col lg:flex-row h-screen w-full bg-zinc-950 text-zinc-100 overflow-hidden font-sans">
      <Helmet>
        <title>Mission Control — Kinetic</title>
        <meta name="description" content="Your live bio-operational triage dashboard." />
      </Helmet>
      {showOnboarding && <OnboardingModal onClose={handleDismissOnboarding} />}
      {/* Left Panel: Operational Liaison Feed */}
      <div className="w-full lg:w-[420px] lg:shrink-0 h-[45vh] lg:h-auto">
        <ChatPanel
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          messages={messages}
          streamingContent={streamingContent}
        />
      </div>

      {/* Right Panel: Mission Control Dashboard */}
      <main className="flex-1 flex flex-col min-w-0 bg-zinc-900/30">
        {/* Top Header */}
        <header className="flex flex-wrap items-center justify-between gap-y-2 border-b border-zinc-800 bg-zinc-950 px-4 md:px-8 py-3 md:py-4">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-bold tracking-tight text-white">Mission Control</h2>
            {health && <StatusBadge status={health.overall_status} />}
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <span className="text-[10px] font-mono text-zinc-400 uppercase">
                {user.display_name}
              </span>
              <button
                onClick={() => {
                  void handleLogout();
                }}
                className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                Sign out
              </button>
            </div>
            {user.tenant === 'demo' && (
              <button
                onClick={() => {
                  void handleSimulateWeek();
                }}
                disabled={isSimulating}
                aria-label={isSimulating ? 'Simulating...' : 'Simulate Week'}
                className="text-[10px] font-bold uppercase tracking-wider text-emerald-500 hover:text-emerald-300 transition-colors disabled:opacity-50"
              >
                {isSimulating ? 'Simulating...' : 'Simulate Week'}
              </button>
            )}
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
        <div className="flex-1 overflow-y-auto p-4 md:p-8" tabIndex={0}>
          {error && (
            <div
              role="alert"
              className="mb-8 rounded-lg border border-status-red/20 bg-status-red/5 p-4"
            >
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-sm font-bold text-status-red">Analysis unavailable</p>
                  <p className="mt-1 text-sm text-zinc-400 truncate">{error}</p>
                </div>
                {lastMessage && (
                  <button
                    onClick={handleRetry}
                    className="shrink-0 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-zinc-200 transition-colors hover:border-zinc-600 hover:text-white"
                  >
                    Retry
                  </button>
                )}
              </div>
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
                  <BioStatusCard
                    data={health.bio}
                    isLoading={isLoading}
                    behavioralSummary={health.behavioral_summary ?? null}
                  />
                  <LogisticsStatusCard data={health.logistics} isLoading={isLoading} />
                  <RelationalStatusCard
                    data={health.relational}
                    isLoading={isLoading}
                    activePauses={health.active_pauses}
                  />
                </div>
              </section>

              {/* Triage Section */}
              <section>
                <TriageList
                  items={health.triage_items}
                  isLoading={isLoading}
                  onCompleteTask={handleCompleteTask}
                />
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

              {/* Weekly Digest Section */}
              <section>
                <WeeklyDigestCard
                  digest={digestData}
                  isLoading={digestLoading}
                  onRefresh={() => void handleRefreshDigest()}
                  isRefreshing={digestRefreshing}
                />
              </section>

              {/* Agent Dispatch Log */}
              <section>
                <AgentDispatchLog entries={agentLog} isLoading={isLoading} />
              </section>
            </div>
          )}
        </div>
      </main>
    </div>
  ) : null;

  return (
    <Routes>
      <Route path="/" element={user ? <Navigate to="/app" replace /> : <LandingPage />} />
      <Route
        path="/login"
        element={
          user ? (
            <Navigate to="/app" replace />
          ) : (
            <LoginScreen onLogin={handleLogin} error={loginError} isLoading={false} />
          )
        }
      />
      <Route path="/app" element={user ? dashboardElement : <Navigate to="/" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
