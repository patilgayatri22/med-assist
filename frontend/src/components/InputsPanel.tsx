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
      <div className="flex flex-col md:flex-row md:items-start gap-6 md:gap-8">
        <div className="flex flex-col sm:flex-row md:flex-col gap-4 md:max-w-[240px] shrink-0">
          <div>
            <h3 className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">
              Vision payload
            </h3>
            <div className="text-sm space-y-1">
              <p><span className="text-[var(--text-muted)]">Drug:</span> {visionPayload.drugName}</p>
              <p><span className="text-[var(--text-muted)]">Dose:</span> {visionPayload.dosage} {visionPayload.unit}</p>
              <p><span className="text-[var(--text-muted)]">Position:</span> {visionPayload.trayPosition}</p>
            </div>
          </div>
          <div className="sm:mt-0 md:mt-0">
            <TrayGrid currentCell={visionPayload.trayPosition} verified={trayVerified} />
          </div>
        </div>
        <div className="flex-1 min-w-0 border-l-0 md:border-l md:border-[var(--border)] md:pl-8">
          <h3 className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-2">
            Patient record
          </h3>
          <dl className="text-sm grid grid-cols-1 sm:grid-cols-[auto_1fr] gap-x-6 gap-y-1.5 sm:gap-y-2">
            <dt className="text-[var(--text-muted)] sm:col-span-1">ID</dt>
            <dd className="font-mono sm:col-span-1">{patientRecord.patientId}</dd>
            <dt className="text-[var(--text-muted)] sm:col-span-1">Ordered</dt>
            <dd className="sm:col-span-1">{patientRecord.orderedDrug} {patientRecord.dose} {patientRecord.route} {patientRecord.frequency}</dd>
            <dt className="text-[var(--text-muted)] sm:col-span-1">Allergies</dt>
            <dd className="sm:col-span-1">{patientRecord.allergies.length ? patientRecord.allergies.join(', ') : 'None'}</dd>
            {patientRecord.highAlert && (
              <dd className="text-highalert font-medium sm:col-span-2">High-alert drug</dd>
            )}
          </dl>
        </div>
      </div>
    </section>
  );
}
