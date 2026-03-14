import { useState, useEffect, useCallback } from 'react';
import type { RunState, DispenseEvent, RunOutcome } from './types/agent';
import { fetchRunState, fetchDispenseLogFromBackend, fetchScenarios } from './api/client';
import { getDispenseEvents } from './api/mockData';
import { fetchDispenseLogFromSupabase } from './api/supabaseLogs';
import { isSupabaseConfigured } from './lib/supabase';
import { getDemoScript } from './demo/demoRunner';
import { Header, type DemoScriptType, type LogsSource } from './components/Header';
import { InputsPanel } from './components/InputsPanel';
import { CheckSequence } from './components/CheckSequence';
import { PickStatus } from './components/PickStatus';
import { HighAlertVerify } from './components/HighAlertVerify';
import { DispenseLog } from './components/DispenseLog';
import { Alerts } from './components/Alerts';
import { OcrUpload } from './components/OcrUpload';

function getStatusLabel(outcome: RunOutcome, armPhase?: RunState['armPhase'], isDemoRunning?: boolean): string {
  if (outcome === 'running') return isDemoRunning ? 'Running checks…' : 'Idle';
  if (outcome === 'dispense') {
    if (armPhase === 'handoff_ready') return 'Handoff ready';
    if (armPhase === 'moving_to_cell' || armPhase === 'gripping' || armPhase === 'returning_to_handoff')
      return `DISPENSE — ${armPhase.replace(/_/g, ' ')}`;
    return 'DISPENSE';
  }
  if (outcome === 'FLAG_HIGH_ALERT_VERIFY') return 'High-alert verification pending';
  return `Halted: ${outcome}`;
}

export default function App() {
  const [runState, setRunState] = useState<RunState | null>(null);
  const [dispenseEvents, setDispenseEvents] = useState<DispenseEvent[]>([]);
  const [isLive, setIsLive] = useState(true);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [demoMode, setDemoMode] = useState<DemoScriptType>('success');
  const [logsSource, setLogsSource] = useState<LogsSource>(() =>
    (import.meta.env.VITE_API_URL as string)?.trim() ? 'backend' : 'demo'
  );
  const [logsError, setLogsError] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<{ scenario_id: string }[]>([]);
  const [scenarioId, setScenarioId] = useState<string | null>(null);

  const backendConfigured = !!(import.meta.env.VITE_API_URL as string)?.trim();

  useEffect(() => {
    fetchScenarios().then(setScenarios);
  }, []);

  const loadEvents = useCallback(async (source: LogsSource) => {
    setLogsError(null);
    if (source === 'supabase') {
      try {
        const events = await fetchDispenseLogFromSupabase();
        setDispenseEvents(events);
      } catch (err) {
        setLogsError(err instanceof Error ? err.message : 'Failed to load logs from Supabase');
        setDispenseEvents([]);
      }
    } else if (source === 'backend') {
      try {
        const events = await fetchDispenseLogFromBackend();
        setDispenseEvents(events);
      } catch (err) {
        setLogsError(err instanceof Error ? err.message : 'Failed to load logs from backend');
        setDispenseEvents([]);
      }
    } else {
      setDispenseEvents(getDispenseEvents());
    }
  }, []);

  const loadInitial = useCallback(async () => {
    const state = await fetchRunState(scenarioId ?? undefined);
    setRunState(state);
    await loadEvents(logsSource);
  }, [logsSource, loadEvents, scenarioId]);

  useEffect(() => {
    loadInitial();
  }, [loadInitial]);

  const handleLogsSourceChange = useCallback(
    (source: LogsSource) => {
      setLogsSource(source);
      loadEvents(source);
    },
    [loadEvents]
  );

  useEffect(() => {
    if (!isDemoMode || !runState) return;

    const { base, steps } = getDemoScript(demoMode);
    let current: RunState = { ...base };
    setRunState(current);

    if (demoMode === 'multi_med') {
      setDispenseEvents([]);
    }

    let timeoutId: ReturnType<typeof setTimeout>;
    function runNext() {
      const step = steps.next();
      if (step.done) return;

      const s = step.value;
      if (s.type === 'delay') {
        timeoutId = setTimeout(runNext, s.ms);
        return;
      }
      if (s.type === 'append_event') {
        setDispenseEvents((prev) => [s.event, ...prev]);
        timeoutId = setTimeout(runNext, 0);
        return;
      }
      current = { ...current, ...s.state };
      setRunState(current);
      timeoutId = setTimeout(runNext, 0);
    }
    runNext();
    return () => clearTimeout(timeoutId);
  }, [isDemoMode, demoMode]);

  const handleToggleDemo = () => {
    if (isDemoMode) {
      setIsDemoMode(false);
      setIsLive(true);
      loadInitial();
    } else {
      setIsDemoMode(true);
      setIsLive(false);
    }
  };

  if (!runState) {
    return (
      <div className="min-h-screen flex items-center justify-center text-[var(--text-muted)]">
        Loading…
      </div>
    );
  }

  const statusLabel = getStatusLabel(runState.outcome, runState.armPhase, isDemoMode);
  const trayVerified = runState.outcome === 'dispense' && runState.checkResults.every((c) => c.status === 'passed');

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        statusLabel={statusLabel}
        outcome={runState.outcome}
        isLive={isLive && !isDemoMode}
        isDemoMode={isDemoMode}
        runTimestamp={runState.timestamp}
        demoScript={demoMode}
        onDemoScriptChange={setDemoMode}
        onToggleDemo={handleToggleDemo}
        logsSource={logsSource}
        onLogsSourceChange={handleLogsSourceChange}
        backendConfigured={backendConfigured}
        supabaseConfigured={isSupabaseConfigured()}
        scenarios={scenarios}
        scenarioId={scenarioId}
        onScenarioIdChange={(id) => {
          setScenarioId(id || null);
          setRunState(null);
        }}
      />
      <main className="flex-1 p-6 max-w-6xl mx-auto w-full space-y-4">
        {logsError && (
          <section className="bg-fail/10 border border-fail rounded-lg p-3 text-sm text-fail" role="alert">
            {logsError}
          </section>
        )}
        <Alerts outcome={runState.outcome} checkResults={runState.checkResults} />
        <OcrUpload />
        <InputsPanel
          visionPayload={runState.visionPayload}
          patientRecord={runState.patientRecord}
          trayVerified={trayVerified}
        />
        <CheckSequence checkResults={runState.checkResults} />
        <HighAlertVerify pending={runState.highAlertVerificationPending ?? false} />
        <PickStatus
          outcome={runState.outcome}
          trayPosition={runState.visionPayload.trayPosition}
          armPhase={runState.armPhase}
          gripConfirmed={runState.gripConfirmed}
        />
        <DispenseLog events={dispenseEvents} />
      </main>
    </div>
  );
}
