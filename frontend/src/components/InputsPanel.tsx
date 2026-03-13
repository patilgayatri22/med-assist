import type { VisionPayload, PatientRecord } from '../types/agent';
import { TrayGrid } from './TrayGrid';

interface InputsPanelProps {
  visionPayload: VisionPayload;
  patientRecord: PatientRecord;
  trayVerified?: boolean;
}

export function InputsPanel({ visionPayload, patientRecord, trayVerified }: InputsPanelProps) {
  return (
    <section className="bg-[var(--bg-panel)] border border-[var(--border)] rounded-lg p-4">
      <h2 className="text-sm font-semibold text-white mb-3">Inputs</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h3 className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">
            Vision payload
          </h3>
          <div className="text-sm space-y-1">
            <p><span className="text-[var(--text-muted)]">Drug:</span> {visionPayload.drugName}</p>
            <p><span className="text-[var(--text-muted)]">Dose:</span> {visionPayload.dosage} {visionPayload.unit}</p>
            <p><span className="text-[var(--text-muted)]">Position:</span> {visionPayload.trayPosition}</p>
          </div>
          <div className="mt-3">
            <TrayGrid currentCell={visionPayload.trayPosition} verified={trayVerified} />
          </div>
        </div>
        <div>
          <h3 className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">
            Patient record
          </h3>
          <div className="text-sm space-y-1">
            <p><span className="text-[var(--text-muted)]">ID:</span> {patientRecord.patientId}</p>
            <p><span className="text-[var(--text-muted)]">Ordered:</span> {patientRecord.orderedDrug} {patientRecord.dose} {patientRecord.route} {patientRecord.frequency}</p>
            <p><span className="text-[var(--text-muted)]">Allergies:</span> {patientRecord.allergies.length ? patientRecord.allergies.join(', ') : 'None'}</p>
            {patientRecord.highAlert && (
              <p className="text-highalert font-medium">High-alert drug</p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
