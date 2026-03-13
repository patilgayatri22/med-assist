import type { RunOutcome, CheckResult } from '../types/agent';

interface AlertsProps {
  outcome: RunOutcome;
  checkResults: CheckResult[];
}

function getAlertMessage(outcome: RunOutcome, checkResults: CheckResult[]): string | null {
  if (outcome === 'running' || outcome === 'dispense') return null;
  const failed = checkResults.find((c) => c.status === 'failed');
  if (failed?.message) return failed.message;
  return `Agent halted: ${outcome}`;
}

export function Alerts({ outcome, checkResults }: AlertsProps) {
  const message = getAlertMessage(outcome, checkResults);
  if (!message) return null;

  return (
    <section className="bg-fail/10 border border-fail rounded-lg p-4" role="alert">
      <h2 className="text-sm font-semibold text-fail mb-1">Alert</h2>
      <p className="text-sm text-[var(--text)]">{message}</p>
    </section>
  );
}
