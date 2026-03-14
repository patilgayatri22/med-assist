import type { RunState, DispenseEvent } from '../types/agent';
import { getInitialRunState, getDispenseEvents } from './mockData';

const MOCK_DELAY_MS = 300;

function getApiBase(): string | undefined {
  const url = import.meta.env.VITE_API_URL as string | undefined;
  return url?.trim() || undefined;
}

async function delay(ms: number = MOCK_DELAY_MS) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function fetchRunState(scenarioId?: string): Promise<RunState> {
  const base = getApiBase();
  if (base) {
    const url = scenarioId
      ? `${base.replace(/\/$/, '')}/api/run-state?scenario_id=${encodeURIComponent(scenarioId)}`
      : `${base.replace(/\/$/, '')}/api/run-state`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Run state failed: ${res.status} ${res.statusText}`);
    const data = await res.json();
    return data as RunState;
  }
  await delay();
  return getInitialRunState();
}

export async function fetchDispenseLog(): Promise<DispenseEvent[]> {
  const base = getApiBase();
  if (base) {
    const res = await fetch(`${base.replace(/\/$/, '')}/api/dispense-log`);
    if (!res.ok) throw new Error(`Dispense log failed: ${res.status} ${res.statusText}`);
    const data = await res.json();
    return Array.isArray(data) ? (data as DispenseEvent[]) : [];
  }
  await delay();
  return getDispenseEvents();
}

/** Fetch dispense log from backend only. Use for "Logs: Backend". Fails if backend not configured. */
export async function fetchDispenseLogFromBackend(): Promise<DispenseEvent[]> {
  const base = getApiBase();
  if (!base) throw new Error('Backend not configured. Set VITE_API_URL in .env.local.');
  const res = await fetch(`${base.replace(/\/$/, '')}/api/dispense-log`);
  if (!res.ok) throw new Error(`Dispense log failed: ${res.status} ${res.statusText}`);
  const data = await res.json();
  return Array.isArray(data) ? (data as DispenseEvent[]) : [];
}

export async function fetchScenarios(): Promise<{ scenario_id: string }[]> {
  const base = getApiBase();
  if (!base) return [];
  const res = await fetch(`${base.replace(/\/$/, '')}/api/scenarios`);
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

/** Result of POST /api/ocr/extract (dispensing label fields). */
export interface OcrExtractResult {
  patient_id?: string | null;
  patient_name?: string | null;
  dob?: string | null;
  room_number?: string | null;
  drug_name_generic?: string | null;
  drug_name_brand?: string | null;
  dosage_value?: string | null;
  dosage_unit?: string | null;
  route?: string | null;
  frequency?: string | null;
  scheduled_time?: string | null;
  prescribed_tablet_count?: string | null;
  high_alert?: string | null;
  lasa_risk?: string | null;
  lasa_pair?: string | null;
  allergies?: string | null;
  special_instructions?: string | null;
  dispensing_status?: string | null;
  prescriber?: string | null;
  confidence_notes?: string | null;
  [key: string]: string | null | undefined;
}

/** Upload an image to extract dispensing label via OCR. Requires backend with OCR enabled. */
export async function uploadLabelForOcr(file: File): Promise<OcrExtractResult> {
  const base = getApiBase();
  if (!base) throw new Error('Backend not configured. Set VITE_API_URL in .env.local.');
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${base.replace(/\/$/, '')}/api/ocr/extract`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `OCR failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<OcrExtractResult>;
}

// For live mode: replace with real fetch or WebSocket
export function subscribeToRunState(
  _onUpdate: (state: RunState) => void
): () => void {
  // No-op for now; when backend exists, open WebSocket and call onUpdate
  return () => {};
}
