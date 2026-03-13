import type { RunState, DispenseEvent, CheckResult } from '../types/agent';
import { CHECK_NAMES } from '../types/agent';

export function makeCheckResults(
  passedUpTo: number,
  failedAt?: number,
  flag?: string,
  message?: string
): CheckResult[] {
  return CHECK_NAMES.map((name, i) => {
    const step = i + 1;
    if (failedAt !== undefined && step === failedAt) {
      return { step, name, status: 'failed' as const, flag, message };
    }
    if (step <= passedUpTo) {
      return { step, name, status: 'passed' as const };
    }
    return { step, name, status: 'pending' as const };
  });
}

export function getInitialRunState(): RunState {
  return {
    id: 'run-1',
    visionPayload: {
      drugName: 'Amoxicillin',
      dosage: '500',
      unit: 'mg',
      trayPosition: 'A1',
    },
    patientRecord: {
      patientId: 'P-10482',
      orderedDrug: 'Amoxicillin',
      dose: '500',
      route: 'PO',
      frequency: 'TID',
      allergies: ['Penicillin'],
      dispensingStatus: 'pending',
      highAlert: false,
    },
    checkResults: makeCheckResults(0),
    outcome: 'running',
    timestamp: new Date().toISOString(),
  };
}

export function getRunStateAllPass(): RunState {
  const base = getInitialRunState();
  return {
    ...base,
    id: 'run-2',
    patientRecord: { ...base.patientRecord, allergies: [] },
    checkResults: makeCheckResults(8),
    outcome: 'dispense',
    armPhase: 'idle',
    timestamp: new Date().toISOString(),
  };
}

const basePatient = {
  patientId: 'P-10482',
  orderedDrug: 'Amoxicillin',
  dose: '500',
  route: 'PO',
  frequency: 'TID',
  allergies: [] as string[],
  dispensingStatus: 'pending' as const,
  highAlert: false,
};

export function getRunStateFlagAllergy(): RunState {
  return {
    ...getInitialRunState(),
    id: 'run-flag',
    visionPayload: { drugName: 'Amoxicillin', dosage: '500', unit: 'mg', trayPosition: 'A1' },
    patientRecord: { ...basePatient, allergies: ['Penicillin'] },
    checkResults: makeCheckResults(0, 1, 'FLAG_ALLERGY', 'Tray drug matches patient allergen: Penicillin'),
    outcome: 'FLAG_ALLERGY',
    timestamp: new Date().toISOString(),
  };
}

export function getRunStateFlagAlreadyDispensed(): RunState {
  return {
    ...getInitialRunState(),
    id: 'run-flag-ad',
    visionPayload: { drugName: 'Lisinopril', dosage: '10', unit: 'mg', trayPosition: 'B1' },
    patientRecord: { ...basePatient, orderedDrug: 'Lisinopril', dose: '10', dispensingStatus: 'dispensed' },
    checkResults: makeCheckResults(1, 2, 'FLAG_ALREADY_DISPENSED', 'Order already dispensed at 08:42 today. Prevents double-dosing.'),
    outcome: 'FLAG_ALREADY_DISPENSED',
    timestamp: new Date().toISOString(),
  };
}

export function getRunStateFlagLasa(): RunState {
  return {
    ...getInitialRunState(),
    id: 'run-flag-lasa',
    visionPayload: { drugName: 'Hydroxyzine', dosage: '25', unit: 'mg', trayPosition: 'A2' },
    patientRecord: { ...basePatient, orderedDrug: 'Hydralazine', dose: '25' },
    checkResults: makeCheckResults(2, 3, 'FLAG_LASA', 'Tray drug Hydroxyzine is look-alike/sound-alike of ordered Hydralazine.'),
    outcome: 'FLAG_LASA',
    timestamp: new Date().toISOString(),
  };
}

export function getRunStateFlagWrongDrug(): RunState {
  return {
    ...getInitialRunState(),
    id: 'run-flag-wrong',
    visionPayload: { drugName: 'Ibuprofen', dosage: '400', unit: 'mg', trayPosition: 'B2' },
    patientRecord: { ...basePatient, orderedDrug: 'Acetaminophen', dose: '500' },
    checkResults: makeCheckResults(3, 4, 'FLAG_WRONG_DRUG', 'Ordered Acetaminophen; tray has Ibuprofen.'),
    outcome: 'FLAG_WRONG_DRUG',
    timestamp: new Date().toISOString(),
  };
}

export function getRunStateFlagOutOfRange(): RunState {
  return {
    ...getInitialRunState(),
    id: 'run-flag-range',
    visionPayload: { drugName: 'Warfarin', dosage: '10', unit: 'mg', trayPosition: 'A1' },
    patientRecord: { ...basePatient, orderedDrug: 'Warfarin', dose: '10' },
    checkResults: makeCheckResults(4, 5, 'FLAG_OUT_OF_RANGE', 'Ordered dose 10 mg exceeds therapeutic range in medication library.'),
    outcome: 'FLAG_OUT_OF_RANGE',
    timestamp: new Date().toISOString(),
  };
}

export function getRunStateFlagWrongDose(): RunState {
  return {
    ...getInitialRunState(),
    id: 'run-flag-dose',
    visionPayload: { drugName: 'Warfarin', dosage: '7', unit: 'mg', trayPosition: 'B1' },
    patientRecord: { ...basePatient, orderedDrug: 'Warfarin', dose: '5' },
    checkResults: makeCheckResults(5, 6, 'FLAG_WRONG_DOSE', 'Ordered 5 mg; tray has 7 mg (DOSE_HIGH).'),
    outcome: 'FLAG_WRONG_DOSE',
    timestamp: new Date().toISOString(),
  };
}

export function getRunStateFlagHighAlertVerify(): RunState {
  const base = getInitialRunState();
  return {
    ...base,
    id: 'run-flag-high',
    visionPayload: { drugName: 'Insulin (regular)', dosage: '10', unit: 'units', trayPosition: 'A1' },
    patientRecord: { ...basePatient, orderedDrug: 'Insulin (regular)', dose: '10', highAlert: true },
    checkResults: makeCheckResults(7),
    outcome: 'FLAG_HIGH_ALERT_VERIFY',
    highAlertVerificationPending: true,
    timestamp: new Date().toISOString(),
  };
}

export function getRunStateFlagPickFailed(): RunState {
  const base = getRunStateAllPass();
  return {
    ...base,
    id: 'run-flag-pick',
    visionPayload: { drugName: 'Metformin', dosage: '500', unit: 'mg', trayPosition: 'A2' },
    patientRecord: { ...basePatient, orderedDrug: 'Metformin', dose: '500' },
    checkResults: makeCheckResults(8),
    outcome: 'FLAG_PICK_FAILED',
    armPhase: 'gripping',
    gripConfirmed: false,
    timestamp: new Date().toISOString(),
  };
}

export function getDispenseEvents(): DispenseEvent[] {
  const now = new Date();
  return [
    {
      id: 'ev-1',
      patientId: 'P-10482',
      drug: 'Lisinopril',
      dose: '10',
      trayPosition: 'B1',
      outcome: 'dispense',
      timestamp: new Date(now.getTime() - 120000).toISOString(),
    },
    {
      id: 'ev-2',
      patientId: 'P-10482',
      drug: 'Metformin',
      dose: '500',
      trayPosition: 'A2',
      outcome: 'dispense',
      timestamp: new Date(now.getTime() - 60000).toISOString(),
    },
    {
      id: 'ev-3',
      patientId: 'P-9912',
      drug: 'Warfarin',
      dose: '5',
      trayPosition: 'B2',
      outcome: 'FLAG_WRONG_DOSE',
      timestamp: new Date(now.getTime() - 30000).toISOString(),
    },
  ];
}
