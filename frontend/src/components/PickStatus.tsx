import type { ArmPhase, RunOutcome } from '../types/agent';

interface PickStatusProps {
  outcome: RunOutcome;
  trayPosition?: string;
  armPhase?: ArmPhase;
  gripConfirmed?: boolean;
}

const ARM_PHASES: ArmPhase[] = [
  'idle',
  'moving_to_cell',
  'gripping',
  'returning_to_handoff',
  'handoff_ready',
];

const ARM_LABELS: Record<ArmPhase, string> = {
  idle: 'Idle',
  moving_to_cell: 'Moving to cell',
  gripping: 'Gripping',
  returning_to_handoff: 'Returning to handoff',
  handoff_ready: 'Handoff ready',
};

export function PickStatus({ outcome, trayPosition, armPhase, gripConfirmed }: PickStatusProps) {
  const showPick = outcome === 'dispense' || outcome === 'FLAG_PICK_FAILED';

  if (!showPick) return null;

  const currentIndex = armPhase ? ARM_PHASES.indexOf(armPhase) : -1;

  return (
    <section className="bg-[var(--bg-panel)] border border-[var(--border)] rounded-lg p-4">
      <h2 className="text-sm font-semibold text-white mb-3">Pick / arm status</h2>
      <div className="flex flex-wrap gap-4 items-center">
        {trayPosition && (
          <p className="text-sm">
            <span className="text-[var(--text-muted)]">Verified position:</span>{' '}
            <span className="font-mono text-white">{trayPosition}</span>
          </p>
        )}
        {armPhase && (
          <p className="text-sm">
            <span className="text-[var(--text-muted)]">Arm:</span>{' '}
            <span className="text-white">{ARM_LABELS[armPhase]}</span>
          </p>
        )}
        {outcome === 'dispense' && gripConfirmed !== undefined && (
          <p className="text-sm">
            <span className="text-[var(--text-muted)]">Grip:</span>{' '}
            <span className={gripConfirmed ? 'text-pass' : 'text-highalert'}>
              {gripConfirmed ? 'Confirmed' : 'Pending'}
            </span>
          </p>
        )}
        {outcome === 'FLAG_PICK_FAILED' && (
          <p className="text-fail text-sm font-medium">Pick failed — empty grasp</p>
        )}
        {outcome === 'dispense' && armPhase === 'handoff_ready' && (
          <p className="text-sm text-[var(--text-muted)] italic">Narrating…</p>
        )}
      </div>
      {outcome === 'dispense' && (
        <div className="mt-3 flex gap-1" aria-label="Arm phase progress">
          {ARM_PHASES.map((phase, i) => (
            <div
              key={phase}
              className={`h-2 flex-1 rounded transition-all duration-300 ${
                i <= currentIndex ? 'bg-pass' : 'bg-[var(--border)]'
              }`}
              title={ARM_LABELS[phase]}
            />
          ))}
        </div>
      )}
    </section>
  );
}
