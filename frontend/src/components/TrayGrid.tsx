interface TrayGridProps {
  currentCell: string;
  verified?: boolean;
}

const ROWS = ['A', 'B', 'C'];
const COLS = [1, 2, 3];

export function TrayGrid({ currentCell, verified }: TrayGridProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="text-xs text-[var(--text-muted)] mb-1">
        Tray {verified && <span className="text-pass">(verified)</span>}
      </div>
      <div className="grid grid-cols-3 gap-1.5 w-fit">
        {ROWS.flatMap((row) =>
          COLS.map((col) => {
            const cellId = `${row}${col}`;
            const isCurrent = currentCell === cellId;
            return (
              <div
                key={cellId}
                className={`w-12 h-12 rounded border flex items-center justify-center text-sm font-mono ${
                  isCurrent
                    ? verified
                      ? 'border-pass bg-pass/15 text-pass'
                      : 'border-highalert bg-highalert/15 text-highalert'
                    : 'border-[var(--border)] bg-[var(--bg-panel)] text-[var(--text-muted)]'
                }`}
                aria-current={isCurrent ? 'true' : undefined}
              >
                {cellId}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
