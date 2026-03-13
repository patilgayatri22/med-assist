import type { DispenseEvent, RunOutcome } from '../types/agent';
import { supabase } from '../lib/supabase';

const TABLE = 'dispense_events';

/** Row shape in Supabase (snake_case). */
export interface DispenseEventRow {
  id: string;
  patient_id: string;
  drug: string;
  dose: string;
  tray_position: string;
  outcome: string;
  timestamp: string; // ISO
}

function rowToEvent(row: DispenseEventRow): DispenseEvent {
  return {
    id: row.id,
    patientId: row.patient_id,
    drug: row.drug,
    dose: row.dose,
    trayPosition: row.tray_position,
    outcome: row.outcome as RunOutcome,
    timestamp: row.timestamp,
  };
}

export async function fetchDispenseLogFromSupabase(): Promise<DispenseEvent[]> {
  if (!supabase) {
    throw new Error('Supabase is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.');
  }
  const { data, error } = await supabase
    .from(TABLE)
    .select('id, patient_id, drug, dose, tray_position, outcome, timestamp')
    .order('timestamp', { ascending: false })
    .limit(100);

  if (error) throw error;
  return (data ?? []).map(rowToEvent);
}
