import type { CheckResult } from '../types/agent';

interface CheckSequenceProps {
  checkResults: CheckResult[];
}

export function CheckSequence({ checkResults }: CheckSequenceProps) {
  return (
    <section className="bg-[var(--bg-panel)] border border-[var(--border)] rounded-lg p-4">
      <h2 className="text-sm font-semibold text-white mb-3">Check sequence</h2>
      <div className="flex flex-wrap gap-2">
        {checkResults.map((c) => (
          <div
            key={c.step}
            className={`px-3 py-2 rounded border text-sm transition-all duration-300 ease-out ${
              c.status === 'passed'
                ? 'border-pass bg-pass/10 text-pass'
                : c.status === 'failed'
                  ? 'border-fail bg-fail/10 text-fail'
                  : 'border-[var(--border)] bg-[var(--bg)] text-[var(--text-muted)]'
            }`}
          >
            <span className="font-mono mr-2">{c.step}.</span>
            <span>{c.name}</span>
            {c.status === 'failed' && c.message && (
              <p className="text-xs mt-1 opacity-90">{c.message}</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
