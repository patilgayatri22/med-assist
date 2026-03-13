import type { DispenseEvent } from '../types/agent';

interface DispenseLogProps {
  events: DispenseEvent[];
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function DispenseLog({ events }: DispenseLogProps) {
  return (
    <section className="bg-[var(--bg-panel)] border border-[var(--border)] rounded-lg p-4">
      <h2 className="text-sm font-semibold text-white mb-3">Dispense event log</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[var(--text-muted)] border-b border-[var(--border)]">
              <th className="pb-2 pr-4">Time</th>
              <th className="pb-2 pr-4">Patient</th>
              <th className="pb-2 pr-4">Drug</th>
              <th className="pb-2 pr-4">Dose</th>
              <th className="pb-2 pr-4">Position</th>
              <th className="pb-2">Outcome</th>
            </tr>
          </thead>
          <tbody>
            {events.map((ev) => (
              <tr key={ev.id} className="border-b border-[var(--border)]/50">
                <td className="py-2 pr-4 font-mono text-xs">{formatTime(ev.timestamp)}</td>
                <td className="py-2 pr-4">{ev.patientId}</td>
                <td className="py-2 pr-4">{ev.drug}</td>
                <td className="py-2 pr-4">{ev.dose}</td>
                <td className="py-2 pr-4 font-mono">{ev.trayPosition}</td>
                <td className={`py-2 ${ev.outcome === 'dispense' ? 'text-pass' : 'text-fail'}`}>
                  {ev.outcome}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
