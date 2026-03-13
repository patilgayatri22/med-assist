import type { RunState, DispenseEvent } from '../types/agent';
import { getInitialRunState, getDispenseEvents } from './mockData';

const MOCK_DELAY_MS = 300;

async function delay(ms: number = MOCK_DELAY_MS) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function fetchRunState(): Promise<RunState> {
  await delay();
  return getInitialRunState();
}

export async function fetchDispenseLog(): Promise<DispenseEvent[]> {
  await delay();
  return getDispenseEvents();
}

// For live mode: replace with real fetch or WebSocket
export function subscribeToRunState(
  _onUpdate: (state: RunState) => void
): () => void {
  // No-op for now; when backend exists, open WebSocket and call onUpdate
  return () => {};
}
