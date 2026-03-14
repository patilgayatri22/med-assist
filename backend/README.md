# MedAssist Backend

API server for run state, dispense log, scenarios, and optional OCR.

## Install (recommended: use venv)

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

This installs the API stack plus OCR deps (easyocr, ollama, pydantic) and **certifi** (used for SSL on macOS to avoid `CERTIFICATE_VERIFY_FAILED`). For OCR you also need the Ollama app and the vision model:

1. Install [Ollama](https://ollama.com) if needed.
2. Pull the vision model (one-time, ~8 GB): `ollama pull llama3.2-vision`

## Run the API

**Important:** uvicorn must be run from the `backend` directory so it can find the `api_server` module.

```bash
cd med-assist/backend
source .venv/bin/activate
uvicorn api_server:app --reload --port 8000
```

Or from anywhere: `./med-assist/backend/run.sh` (after activating the venv).

- **Run state:** `GET /api/run-state?scenario_id=SCN-001` — returns the frontend `RunState` for that scenario.
- **Dispense log:** `GET /api/dispense-log` — list of dispense events (in-memory; append via `POST /api/dispense-log`).
- **Scenarios:** `GET /api/scenarios` — list of scenario IDs.
- **OCR (optional):** `POST /api/ocr/extract` — upload a dispensing label image; returns extracted fields. See **OCR** section below.

## Frontend

In the frontend `.env.local` set:

```
VITE_API_URL=http://localhost:8000
```

Then the dashboard will load run state and dispense log from this backend.

## OCR (prescription_ocr)

To enable `/api/ocr/extract` (you can run the API from `backend/` as usual):

1. Install OCR deps in the same env you use for the API:
   ```bash
   cd backend
   pip install easyocr ollama
   ```
2. Install [Ollama](https://ollama.com) and start it.
3. Pull the vision model (one-time, ~8 GB): `ollama pull llama3.2-vision`
4. Start the API from **backend/** as above; `prescription_ocr` (in the med-assist root) is loaded automatically.

If OCR deps are missing or Ollama isn’t running, the endpoint returns 503 with instructions; the rest of the API still works.

**Why extraction is slow:** Models are **not** re-downloaded on each request. EasyOCR is loaded once per API process (first run only); Ollama keeps the vision model in memory. The delay is from running EasyOCR on the image plus vision-model inference each time — typically 15–60+ seconds per image depending on hardware. The first extraction after starting the API (or after Ollama has unloaded the model) can be slower while models load into RAM.

## Dispensing labels as input

You can run scenarios from label images or JSON in a **dispensing_labels** folder instead of the default CSVs:

1. Create or use the folder: `backend/dispensing_labels/`
2. Add **images** (`.png`, `.jpg`, `.jpeg`, `.webp`) and/or **JSON** files (DispensingOrder-like structure).
3. On startup, the backend loads scenarios from this folder when present:
   - **Images:** OCR is run via `prescription_ocr` if available; each image becomes one scenario (order + tray from the same label).
   - **JSON:** Each file is loaded as one scenario (same shape as OCR output).
4. Scenario IDs are derived from filenames (e.g. `label_01.png` → `label_01`). Tray positions are assigned as A1, A2, … in file order.

If the folder is missing or yields no scenarios, the backend falls back to `patient_medication_orders.csv` and `tray_scenarios.csv`.
