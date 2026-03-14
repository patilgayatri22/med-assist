import { useState, useRef } from 'react';
import { uploadLabelForOcr, type OcrExtractResult } from '../api/client';

function getApiBase(): boolean {
  const url = (import.meta.env.VITE_API_URL as string)?.trim();
  return !!url;
}

export function OcrUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<OcrExtractResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  if (!getApiBase()) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    setFile(f ?? null);
    setResult(null);
    setError(null);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await uploadLabelForOcr(file);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OCR failed');
    } finally {
      setLoading(false);
    }
  };

  const displayFields = result
    ? [
        ['Patient', result.patient_name, result.patient_id, result.room_number],
        ['Drug', result.drug_name_generic || result.drug_name_brand, `${result.dosage_value || ''} ${result.dosage_unit || ''}`.trim()],
        ['Route / Frequency', result.route, result.frequency, result.scheduled_time],
        ['Allergies', result.allergies],
        ['High alert', result.high_alert],
        ['Prescriber', result.prescriber],
        ['Notes', result.confidence_notes],
      ].filter(([, ...vals]) => vals.some((v) => v != null && String(v).trim() !== ''))
    : [];

  return (
    <section className="bg-[var(--bg-panel)] border border-[var(--border)] rounded-lg p-4">
      <h2 className="text-sm font-semibold text-white mb-3">Dispensing label OCR</h2>
      <p className="text-xs text-[var(--text-muted)] mb-3">
        Upload a label image to extract patient and medication fields (requires backend with Ollama + llama3.2-vision).
      </p>
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="text-sm text-[var(--text-muted)] file:mr-2 file:py-1.5 file:px-3 file:rounded file:border-0 file:bg-white/10 file:text-white file:font-medium file:cursor-pointer file:transition-colors file:hover:bg-white/15 file:active:bg-white/20 file:[box-shadow:inset_0_0_0_1px_var(--border)]"
          aria-label="Choose label image"
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!file || loading}
          className="text-sm font-medium px-3 py-1.5 rounded border border-[var(--border)] bg-white/5 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-white/10"
        >
          {loading ? 'Extracting…' : 'Extract'}
        </button>
      </div>
      {error && (
        <div className="mb-3 p-2 rounded bg-fail/10 border border-fail text-sm text-fail" role="alert">
          {error}
        </div>
      )}
      {result && displayFields.length > 0 && (
        <div className="text-sm border border-[var(--border)] rounded p-3 bg-[var(--bg)] space-y-2">
          {displayFields.map(([label, ...vals], i) => (
            <div key={i}>
              <span className="text-[var(--text-muted)] font-medium">{label}:</span>{' '}
              {vals.filter(Boolean).join(' · ')}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
