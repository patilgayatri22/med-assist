import { useState, useEffect } from 'react';
import type { RunOutcome } from '../types/agent';
import type { DemoMode } from '../demo/demoRunner';

export type DemoScriptType = DemoMode;

const DEMO_OPTIONS: { value: DemoMode; label: string }[] = [
  { value: 'success', label: 'All pass (dispense)' },
  { value: 'multi_med', label: 'Multiple meds (2 dispense, 1 halt)' },
  { value: 'flag_allergy', label: 'Halt: Allergy' },
  { value: 'flag_already_dispensed', label: 'Halt: Already dispensed' },
  { value: 'flag_lasa', label: 'Halt: LASA confusion' },
  { value: 'flag_wrong_drug', label: 'Halt: Wrong drug' },
  { value: 'flag_out_of_range', label: 'Halt: Out of range' },
  { value: 'flag_wrong_dose', label: 'Halt: Wrong dose' },
  { value: 'flag_high_alert_verify', label: 'High-alert (verify pending)' },
  { value: 'flag_pick_failed', label: 'Pick failed (empty grasp)' },
];

export type LogsSource = 'demo' | 'backend' | 'supabase';

interface HeaderProps {
  statusLabel: string;
  outcome?: RunOutcome;
  isLive: boolean;
  isDemoMode: boolean;
  runTimestamp?: string;
  demoScript: DemoScriptType;
  onDemoScriptChange: (script: DemoScriptType) => void;
  onToggleDemo: () => void;
  logsSource: LogsSource;
  onLogsSourceChange: (source: LogsSource) => void;
  backendConfigured: boolean;
  supabaseConfigured: boolean;
  scenarios?: { scenario_id: string }[];
  scenarioId?: string | null;
  onScenarioIdChange?: (id: string) => void;
}

function getStatusColor(outcome?: RunOutcome): string {
  if (!outcome || outcome === 'running') return 'text-[var(--text-muted)]';
  if (outcome === 'dispense') return 'text-pass';
  if (outcome === 'FLAG_HIGH_ALERT_VERIFY') return 'text-highalert';
  return 'text-fail';
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatLiveTime(date: Date): string {
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function Header({
  statusLabel,
  outcome,
  isLive,
  isDemoMode,
  runTimestamp,
  demoScript,
  onDemoScriptChange,
  onToggleDemo,
  logsSource,
  onLogsSourceChange,
  backendConfigured,
  supabaseConfigured,
  scenarios = [],
  scenarioId,
  onScenarioIdChange,
}: HeaderProps) {
  const hasBackendScenarios = scenarios.length > 0;
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <header className="border-b border-[var(--border)] bg-[var(--bg-panel)] px-6 py-4 flex items-center justify-between flex-wrap gap-3">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold text-white tracking-tight">MedAssist Monitor</h1>
        <span
          className={`text-sm font-medium ${getStatusColor(outcome)}`}
          data-testid="status-label"
        >
          {statusLabel}
        </span>
        <span className="text-xs text-[var(--text-muted)] font-mono" aria-live="polite" title="Current time">
          {formatLiveTime(now)}
        </span>
        {runTimestamp && isDemoMode && (
          <span className="text-xs text-[var(--text-muted)] font-mono" title="Run started">
            Started {formatTime(runTimestamp)}
          </span>
        )}
        {isLive && (
          <span className="live-indicator text-xs text-pass font-medium px-2 py-0.5 rounded bg-pass/10">
            Live
          </span>
        )}
      </div>
      <div className="flex items-center gap-2">
        {!isDemoMode && (
          <>
            {hasBackendScenarios && (
              <select
                value={scenarioId ?? ''}
                onChange={(e) => onScenarioIdChange?.(e.target.value)}
                className="text-sm bg-[var(--bg)] border border-[var(--border)] rounded px-2 py-1.5 text-[var(--text)] font-mono max-w-[140px]"
                aria-label="Backend scenario"
                title="Scenario from backend"
              >
                <option value="">Default</option>
                {scenarios.map((s) => (
                  <option key={s.scenario_id} value={s.scenario_id}>
                    {s.scenario_id}
                  </option>
                ))}
              </select>
            )}
            <select
              value={demoScript}
              onChange={(e) => onDemoScriptChange(e.target.value as DemoScriptType)}
              className="text-sm bg-[var(--bg)] border border-[var(--border)] rounded px-2 py-1.5 text-[var(--text)] max-w-[220px]"
              aria-label="Demo script"
            >
              {DEMO_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <select
              value={logsSource}
              onChange={(e) => onLogsSourceChange(e.target.value as LogsSource)}
              className="text-sm bg-[var(--bg)] border border-[var(--border)] rounded px-2 py-1.5 text-[var(--text)]"
              aria-label="Logs source"
              title={
                logsSource === 'backend' && !backendConfigured
                  ? 'Set VITE_API_URL to use backend logs'
                  : !supabaseConfigured && logsSource === 'supabase'
                    ? 'Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to use Supabase'
                    : undefined
              }
            >
              <option value="demo">Logs: Demo</option>
              <option value="backend" disabled={!backendConfigured}>
                Logs: Backend
              </option>
              <option value="supabase" disabled={!supabaseConfigured}>
                Logs: Supabase
              </option>
            </select>
          </>
        )}
        <button
          type="button"
          onClick={onToggleDemo}
          className={`text-sm font-medium px-3 py-1.5 rounded border ${
            isDemoMode
              ? 'bg-highalert/20 border-highalert text-highalert'
              : 'border-[var(--border)] text-[var(--text-muted)] hover:bg-white/5'
          }`}
        >
          {isDemoMode ? 'Stop demo' : 'Run demo'}
        </button>
      </div>
    </header>
  );
}
