"""
MedAssist HTTP API — run state, dispense log, scenarios, and OCR.
Run with: uvicorn api_server:app --reload --port 8000
"""
import os
import sys
from pathlib import Path

# Use certifi CA bundle so HTTPS works on macOS (avoids SSL: CERTIFICATE_VERIFY_FAILED)
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except Exception:
    pass

# So prescription_ocr (med-assist root) can be imported when running from backend/
_med_assist_root = Path(__file__).resolve().parent.parent
if str(_med_assist_root) not in sys.path:
    sys.path.insert(0, str(_med_assist_root))

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from agent_runner import MedAssistRunner

app = FastAPI(title="MedAssist API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory dispense log (append when backend records a dispense)
_dispense_events: List[Dict[str, Any]] = []
_runner: Optional[MedAssistRunner] = None


def get_runner() -> MedAssistRunner:
    global _runner
    if _runner is None:
        _runner = MedAssistRunner()
    return _runner


def _tray_with_expired(tray: Dict[str, Any]) -> Dict[str, Any]:
    """Set tray['expired'] from tray_expiry_date if in the past."""
    out = dict(tray)
    exp = out.get("tray_expiry_date")
    if exp:
        try:
            from datetime import date
            if isinstance(exp, str) and len(exp) >= 10:
                y, m, d = int(exp[:4]), int(exp[5:7]), int(exp[8:10])
                out["expired"] = date(y, m, d) < date.today()
            else:
                out["expired"] = False
        except Exception:
            out["expired"] = False
    else:
        out["expired"] = False
    return out


def _rule_to_run_state(scenario_id: str, tray: Dict[str, Any], order: Dict[str, Any], rule_result: Dict[str, Any]) -> Dict[str, Any]:
    """Build frontend RunState from backend rule result + tray + order."""

    check_results = rule_result.get("check_results", [])
    outcome = rule_result.get("outcome", "running")
    if outcome == "dispense":
        outcome = "dispense"
    elif outcome not in (
        "FLAG_ALLERGY", "FLAG_ALREADY_DISPENSED", "FLAG_LASA", "FLAG_WRONG_DRUG",
        "FLAG_OUT_OF_RANGE", "FLAG_WRONG_DOSE", "FLAG_HIGH_ALERT_VERIFY", "FLAG_PICK_FAILED",
    ):
        fc = rule_result.get("flag_code", "NONE")
        if fc == "NONE" and rule_result.get("status") == "proceed":
            outcome = "dispense"
        else:
            outcome = f"FLAG_{fc}" if fc != "NONE" else "running"

    def dose_val(d: Dict, vk: str, uk: str) -> str:
        v = d.get(vk)
        u = d.get(uk) or ""
        if v is None or (isinstance(v, float) and (v != v)):
            return ""
        return f"{v}{u}".replace(" ", "").strip()

    vision_payload = {
        "drugName": (tray.get("tray_drug") or order.get("drug_name_generic") or "").strip() or "—",
        "dosage": str(tray.get("tray_dose_value") or order.get("dosage_value") or "").strip(),
        "unit": (tray.get("tray_dose_unit") or order.get("dosage_unit") or "").strip(),
        "trayPosition": str(tray.get("tray_position", "")),
    }
    allergies_raw = order.get("allergies") or ""
    if allergies_raw and not (isinstance(allergies_raw, float) and allergies_raw != allergies_raw):
        allergies = [a.strip() for a in str(allergies_raw).split(",") if a.strip() and a.strip().lower() != "nan"]
    else:
        allergies = []
    patient_record = {
        "patientId": str(order.get("patient_id", "")),
        "orderedDrug": (order.get("drug_name_generic") or tray.get("ordered_drug") or "").strip(),
        "dose": dose_val(order, "dosage_value", "dosage_unit") or dose_val(tray, "ordered_dose_value", "ordered_dose_unit"),
        "route": (order.get("route") or "PO").strip(),
        "frequency": (order.get("frequency") or "").strip(),
        "allergies": allergies,
        "dispensingStatus": (order.get("dispensing_status") or "pending").strip().lower(),
        "highAlert": order.get("high_alert") in (True, "True", "true", "1"),
    }
    checks = []
    for c in check_results:
        checks.append({
            "step": c["step"],
            "name": c["name"],
            "status": c["status"],
            "flag": c.get("flag"),
            "message": c.get("message"),
        })

    return {
        "id": f"run-{scenario_id}",
        "visionPayload": vision_payload,
        "patientRecord": patient_record,
        "checkResults": checks,
        "outcome": outcome,
        "highAlertVerificationPending": outcome == "FLAG_HIGH_ALERT_VERIFY",
        "gripConfirmed": None,
        "armPhase": "idle" if outcome != "dispense" else "handoff_ready",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/scenarios")
def list_scenarios() -> List[Dict[str, str]]:
    """List available scenario IDs for run-state."""
    runner = get_runner()
    ids = runner.trays["scenario_id"].tolist()
    return [{"scenario_id": str(s)} for s in ids]


@app.get("/api/run-state")
def get_run_state(scenario_id: Optional[str] = None) -> Dict[str, Any]:
    """Get RunState for the given scenario (or first). Frontend uses this for initial load and live mode."""
    runner = get_runner()
    if not scenario_id:
        scenario_id = runner.trays["scenario_id"].iloc[0]
    try:
        tray = _tray_with_expired(runner.get_scenario(str(scenario_id)))
        order = runner.get_order(tray["patient_id"])
        result = runner.run_by_scenario_id(str(scenario_id), include_llm_summary=False)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    rule_result = result["rule_result"]
    return _rule_to_run_state(str(scenario_id), tray, order, rule_result)


@app.get("/api/dispense-log")
def get_dispense_log() -> List[Dict[str, Any]]:
    """Dispense events for the dashboard. Optional: persist in DB later."""
    return _dispense_events


@app.post("/api/dispense-log")
def append_dispense_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Append a dispense event (e.g. from robot or simulator)."""
    event.setdefault("id", f"ev-{len(_dispense_events) + 1}")
    event.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
    _dispense_events.insert(0, event)
    return {"ok": True, "id": event["id"]}


# ----- OCR (optional: depends on prescription_ocr) -----
def _ocr_available() -> bool:
    try:
        import prescription_ocr  # noqa: F401
        return True
    except Exception:
        return False


def _ocr_unavailable_message() -> str:
    return (
        "OCR not available. From med-assist/backend: pip install easyocr ollama. "
        "Then install Ollama (https://ollama.com), run it, and run: ollama pull llama3.2-vision"
    )


@app.post("/api/ocr/extract")
async def ocr_extract(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Extract dispensing label from image using OCR. Requires prescription_ocr and ollama/easyocr."""
    if not _ocr_available():
        raise HTTPException(status_code=503, detail=_ocr_unavailable_message())
    import tempfile
    import prescription_ocr
    suffix = Path(file.filename or "image").suffix or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp.flush()
        path = Path(tmp.name)
    try:
        order = prescription_ocr.extract_label(path)
        return order.model_dump()
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        path.unlink(missing_ok=True)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}
