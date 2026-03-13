import type { RunState, DispenseEvent } from '../types/agent';
import {
  getRunStateAllPass,
  getRunStateFlagAllergy,
  getRunStateFlagAlreadyDispensed,
  getRunStateFlagLasa,
  getRunStateFlagWrongDrug,
  getRunStateFlagOutOfRange,
  getRunStateFlagWrongDose,
  getRunStateFlagHighAlertVerify,
  getRunStateFlagPickFailed,
  makeCheckResults,
} from '../api/mockData';

export type DemoScriptStep =
  | { type: 'run'; state: Partial<RunState> }
  | { type: 'delay'; ms: number }
  | { type: 'append_event'; event: DispenseEvent };

export type DemoMode =
  | 'success'
  | 'flag_allergy'
  | 'flag_already_dispensed'
  | 'flag_lasa'
  | 'flag_wrong_drug'
  | 'flag_out_of_range'
  | 'flag_wrong_dose'
  | 'flag_high_alert_verify'
  | 'flag_pick_failed'
  | 'multi_med';

/** Scripted sequence: checks pass one-by-one -> DISPENSE -> arm phases -> handoff. */
export function* runSuccessScript(): Generator<DemoScriptStep, void, void> {
  for (let i = 0; i <= 8; i++) {
    yield {
      type: 'run',
      state: {
        checkResults: makeCheckResults(i),
        outcome: (i < 8 ? 'running' : 'dispense') as RunState['outcome'],
      },
    };
    yield { type: 'delay', ms: 600 };
  }

  yield { type: 'run', state: { outcome: 'dispense', armPhase: 'moving_to_cell' } };
  yield { type: 'delay', ms: 800 };
  yield { type: 'run', state: { armPhase: 'gripping' } };
  yield { type: 'delay', ms: 500 };
  yield { type: 'run', state: { gripConfirmed: true, armPhase: 'returning_to_handoff' } };
  yield { type: 'delay', ms: 700 };
  yield { type: 'run', state: { armPhase: 'handoff_ready' } };
}

/** Helper: run N checks then fail at step failedAt with flag and message. */
function* runFlagAtStep(
  failedAt: number,
  flag: RunState['outcome'],
  message: string
): Generator<DemoScriptStep, void, void> {
  for (let i = 0; i < failedAt; i++) {
    yield { type: 'run', state: { checkResults: makeCheckResults(i), outcome: 'running' } };
    yield { type: 'delay', ms: 400 };
  }
  yield {
    type: 'run',
    state: {
      checkResults: makeCheckResults(failedAt - 1, failedAt, flag, message),
      outcome: flag,
    },
  };
}

export function* runFlagAllergyScript(): Generator<DemoScriptStep, void, void> {
  yield { type: 'delay', ms: 400 };
  yield {
    type: 'run',
    state: {
      checkResults: makeCheckResults(0, 1, 'FLAG_ALLERGY', 'Tray drug matches patient allergen: Penicillin'),
      outcome: 'FLAG_ALLERGY',
    },
  };
}

function* runFlagAlreadyDispensedScript(): Generator<DemoScriptStep, void, void> {
  yield* runFlagAtStep(2, 'FLAG_ALREADY_DISPENSED', 'Order already dispensed at 08:42 today. Prevents double-dosing.');
}

function* runFlagLasaScript(): Generator<DemoScriptStep, void, void> {
  yield* runFlagAtStep(3, 'FLAG_LASA', 'Tray drug Hydroxyzine is look-alike/sound-alike of ordered Hydralazine.');
}

function* runFlagWrongDrugScript(): Generator<DemoScriptStep, void, void> {
  yield* runFlagAtStep(4, 'FLAG_WRONG_DRUG', 'Ordered Acetaminophen; tray has Ibuprofen.');
}

function* runFlagOutOfRangeScript(): Generator<DemoScriptStep, void, void> {
  yield* runFlagAtStep(5, 'FLAG_OUT_OF_RANGE', 'Ordered dose 10 mg exceeds therapeutic range in medication library.');
}

function* runFlagWrongDoseScript(): Generator<DemoScriptStep, void, void> {
  yield* runFlagAtStep(6, 'FLAG_WRONG_DOSE', 'Ordered 5 mg; tray has 7 mg (DOSE_HIGH).');
}

function* runFlagHighAlertVerifyScript(): Generator<DemoScriptStep, void, void> {
  for (let i = 0; i <= 7; i++) {
    yield {
      type: 'run',
      state: {
        checkResults: makeCheckResults(i),
        outcome: (i < 7 ? 'running' : 'FLAG_HIGH_ALERT_VERIFY') as RunState['outcome'],
        highAlertVerificationPending: i === 7,
      },
    };
    yield { type: 'delay', ms: 500 };
  }
}

function* runFlagPickFailedScript(): Generator<DemoScriptStep, void, void> {
  for (let i = 0; i <= 8; i++) {
    yield { type: 'run', state: { checkResults: makeCheckResults(i), outcome: i < 8 ? 'running' : 'dispense' } };
    yield { type: 'delay', ms: 400 };
  }
  yield { type: 'run', state: { outcome: 'dispense', armPhase: 'moving_to_cell' } };
  yield { type: 'delay', ms: 600 };
  yield { type: 'run', state: { armPhase: 'gripping' } };
  yield { type: 'delay', ms: 500 };
  yield { type: 'run', state: { outcome: 'FLAG_PICK_FAILED', gripConfirmed: false } };
}

/** Multi-med: run 1 dispenses, run 2 dispenses, run 3 halts on FLAG_WRONG_DOSE. Appends to event log on each dispense. */
function* runMultiMedScript(): Generator<DemoScriptStep, void, void> {
  const now = () => new Date().toISOString();

  // Run 1: Lisinopril — full success
  let run1 = getRunStateAllPass();
  run1 = {
    ...run1,
    visionPayload: { drugName: 'Lisinopril', dosage: '10', unit: 'mg', trayPosition: 'A1' },
    patientRecord: { ...run1.patientRecord, orderedDrug: 'Lisinopril', dose: '10' },
    checkResults: makeCheckResults(0),
    outcome: 'running',
    armPhase: undefined,
    gripConfirmed: undefined,
  };
  for (let i = 0; i <= 8; i++) {
    yield { type: 'run', state: { ...run1, checkResults: makeCheckResults(i), outcome: i < 8 ? 'running' : 'dispense' } };
    yield { type: 'delay', ms: 450 };
  }
  yield { type: 'run', state: { outcome: 'dispense', armPhase: 'moving_to_cell' } };
  yield { type: 'delay', ms: 600 };
  yield { type: 'run', state: { armPhase: 'gripping' } };
  yield { type: 'delay', ms: 400 };
  yield { type: 'run', state: { gripConfirmed: true, armPhase: 'returning_to_handoff' } };
  yield { type: 'delay', ms: 500 };
  yield { type: 'run', state: { armPhase: 'handoff_ready' } };
  yield { type: 'append_event', event: { id: 'multi-1', patientId: 'P-10482', drug: 'Lisinopril', dose: '10', trayPosition: 'A1', outcome: 'dispense', timestamp: now() } };
  yield { type: 'delay', ms: 800 };

  // Run 2: Metformin — full success
  let run2 = getRunStateAllPass();
  run2 = {
    ...run2,
    visionPayload: { drugName: 'Metformin', dosage: '500', unit: 'mg', trayPosition: 'B1' },
    patientRecord: { ...run2.patientRecord, orderedDrug: 'Metformin', dose: '500' },
    checkResults: makeCheckResults(0),
    outcome: 'running',
    armPhase: undefined,
    gripConfirmed: undefined,
  };
  for (let i = 0; i <= 8; i++) {
    yield { type: 'run', state: { ...run2, checkResults: makeCheckResults(i), outcome: i < 8 ? 'running' : 'dispense' } };
    yield { type: 'delay', ms: 450 };
  }
  yield { type: 'run', state: { outcome: 'dispense', armPhase: 'moving_to_cell' } };
  yield { type: 'delay', ms: 600 };
  yield { type: 'run', state: { armPhase: 'gripping' } };
  yield { type: 'delay', ms: 400 };
  yield { type: 'run', state: { gripConfirmed: true, armPhase: 'returning_to_handoff' } };
  yield { type: 'delay', ms: 500 };
  yield { type: 'run', state: { armPhase: 'handoff_ready' } };
  yield { type: 'append_event', event: { id: 'multi-2', patientId: 'P-10482', drug: 'Metformin', dose: '500', trayPosition: 'B1', outcome: 'dispense', timestamp: now() } };
  yield { type: 'delay', ms: 800 };

  // Run 3: Warfarin — fail at dose match
  const run3 = getRunStateFlagWrongDose();
  const base3: RunState = { ...run3, checkResults: makeCheckResults(0), outcome: 'running' };
  for (let i = 0; i < 6; i++) {
    yield { type: 'run', state: { ...base3, checkResults: makeCheckResults(i), outcome: 'running' } };
    yield { type: 'delay', ms: 450 };
  }
  yield {
    type: 'run',
    state: {
      ...base3,
      checkResults: makeCheckResults(5, 6, 'FLAG_WRONG_DOSE', 'Ordered 5 mg; tray has 7 mg (DOSE_HIGH).'),
      outcome: 'FLAG_WRONG_DOSE',
    },
  };
}

export function getDemoScript(mode: DemoMode): {
  base: RunState;
  steps: Generator<DemoScriptStep, void, void>;
} {
  const withRunning = (full: RunState): RunState => ({
    ...full,
    checkResults: makeCheckResults(0),
    outcome: 'running',
    armPhase: undefined,
    gripConfirmed: undefined,
    highAlertVerificationPending: undefined,
  });

  switch (mode) {
    case 'success': {
      const base = withRunning(getRunStateAllPass());
      return { base, steps: runSuccessScript() };
    }
    case 'flag_allergy': {
      const base = withRunning(getRunStateFlagAllergy());
      return { base, steps: runFlagAllergyScript() };
    }
    case 'flag_already_dispensed': {
      const full = getRunStateFlagAlreadyDispensed();
      const base: RunState = { ...full, checkResults: makeCheckResults(0), outcome: 'running' };
      return { base, steps: runFlagAlreadyDispensedScript() };
    }
    case 'flag_lasa': {
      const full = getRunStateFlagLasa();
      const base: RunState = { ...full, checkResults: makeCheckResults(0), outcome: 'running' };
      return { base, steps: runFlagLasaScript() };
    }
    case 'flag_wrong_drug': {
      const full = getRunStateFlagWrongDrug();
      const base: RunState = { ...full, checkResults: makeCheckResults(0), outcome: 'running' };
      return { base, steps: runFlagWrongDrugScript() };
    }
    case 'flag_out_of_range': {
      const full = getRunStateFlagOutOfRange();
      const base: RunState = { ...full, checkResults: makeCheckResults(0), outcome: 'running' };
      return { base, steps: runFlagOutOfRangeScript() };
    }
    case 'flag_wrong_dose': {
      const full = getRunStateFlagWrongDose();
      const base: RunState = { ...full, checkResults: makeCheckResults(0), outcome: 'running' };
      return { base, steps: runFlagWrongDoseScript() };
    }
    case 'flag_high_alert_verify': {
      const full = getRunStateFlagHighAlertVerify();
      const base: RunState = { ...full, checkResults: makeCheckResults(0), outcome: 'running', highAlertVerificationPending: false };
      return { base, steps: runFlagHighAlertVerifyScript() };
    }
    case 'flag_pick_failed': {
      const full = getRunStateFlagPickFailed();
      const base: RunState = { ...full, checkResults: makeCheckResults(0), outcome: 'running', armPhase: undefined, gripConfirmed: undefined };
      return { base, steps: runFlagPickFailedScript() };
    }
    case 'multi_med': {
      const base = withRunning({
        ...getRunStateAllPass(),
        visionPayload: { drugName: 'Lisinopril', dosage: '10', unit: 'mg', trayPosition: 'A1' },
        patientRecord: { ...getRunStateAllPass().patientRecord, orderedDrug: 'Lisinopril', dose: '10' },
      });
      return { base, steps: runMultiMedScript() };
    }
    default:
      return getDemoScript('success');
  }
}
