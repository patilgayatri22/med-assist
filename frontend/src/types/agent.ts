// Agent decision flow & SO-101 pick mechanism types (aligned with MedAssist spec)

export interface VisionPayload {
  drugName: string;
  dosage: string;
  unit: string;
  trayPosition: string; // e.g. "A1", "B2"
}

export interface PatientRecord {
  patientId: string;
  orderedDrug: string;
  dose: string;
  route: string;
  frequency: string;
  allergies: string[];
  dispensingStatus: 'pending' | 'dispensed';
  highAlert?: boolean;
}

export type CheckStatus = 'pending' | 'passed' | 'failed';

export interface CheckResult {
  step: number;
  name: string;
  status: CheckStatus;
  flag?: string;
  message?: string;
}

export type ArmPhase =
  | 'idle'
  | 'moving_to_cell'
  | 'gripping'
  | 'returning_to_handoff'
  | 'handoff_ready';

export type RunOutcome =
  | 'running'
  | 'dispense'
  | 'FLAG_ALLERGY'
  | 'FLAG_ALREADY_DISPENSED'
  | 'FLAG_LASA'
  | 'FLAG_WRONG_DRUG'
  | 'FLAG_OUT_OF_RANGE'
  | 'FLAG_WRONG_DOSE'
  | 'FLAG_HIGH_ALERT_VERIFY'
  | 'FLAG_PICK_FAILED';

export interface RunState {
  id: string;
  visionPayload: VisionPayload;
  patientRecord: PatientRecord;
  checkResults: CheckResult[];
  outcome: RunOutcome;
  highAlertVerificationPending?: boolean;
  gripConfirmed?: boolean;
  armPhase?: ArmPhase;
  timestamp: string; // ISO
}

export interface DispenseEvent {
  id: string;
  patientId: string;
  drug: string;
  dose: string;
  trayPosition: string;
  outcome: RunOutcome;
  timestamp: string;
}

// Check sequence order (1–8)
export const CHECK_NAMES = [
  'Allergy',
  'Already Dispensed',
  'LASA Confusion',
  'Drug Match',
  'Out of Range',
  'Dose Match',
  'High Alert',
  'All Clear',
] as const;
