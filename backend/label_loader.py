"""
Load MedAssist order + tray scenarios from a dispensing_labels folder.

Supports:
- Image files (.png, .jpg, .jpeg, .webp): OCR via prescription_ocr if available.
- JSON files: direct load of DispensingOrder-like structure.

Each file becomes one scenario: the same extracted data is used as both the
patient order and the tray (so the rule engine verifies the label against itself).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


# Image extensions we treat as label images
LABEL_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _ocr_available() -> bool:
    try:
        import sys
        backend_dir = Path(__file__).resolve().parent
        parent = backend_dir.parent
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        import prescription_ocr  # noqa: F401
        return True
    except Exception:
        return False


def _extract_from_image(image_path: Path) -> Dict[str, Any]:
    """Run OCR on image and return DispensingOrder as dict. Raises if OCR not available."""
    import sys
    backend_dir = Path(__file__).resolve().parent
    parent = backend_dir.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    import prescription_ocr
    order = prescription_ocr.extract_label(image_path)
    return order.model_dump()


def _order_row_from_extraction(data: Dict[str, Any], scenario_id: str) -> Dict[str, Any]:
    """Build one patient_medication_orders row from extracted label data."""
    patient_id = (data.get("patient_id") or "").strip() or scenario_id
    return {
        "patient_id": patient_id,
        "patient_name": data.get("patient_name"),
        "dob": data.get("dob"),
        "room_number": data.get("room_number"),
        "drug_name_generic": data.get("drug_name_generic"),
        "drug_name_brand": data.get("drug_name_brand"),
        "dosage_value": data.get("dosage_value"),
        "dosage_unit": data.get("dosage_unit"),
        "route": data.get("route") or "oral",
        "frequency": data.get("frequency"),
        "scheduled_time": data.get("scheduled_time"),
        "dispensing_status": (data.get("dispensing_status") or "pending").strip().lower(),
        "high_alert": data.get("high_alert"),
        "lasa_risk": data.get("lasa_risk"),
        "lasa_pair": data.get("lasa_pair"),
        "allergies": data.get("allergies"),
        "special_instructions": data.get("special_instructions"),
        "prescriber": data.get("prescriber"),
        "prescribed_tablet_count": data.get("prescribed_tablet_count"),
    }


def _tray_row_from_extraction(
    data: Dict[str, Any],
    scenario_id: str,
    tray_position: str,
    scenario_type: str = "FROM_LABEL",
) -> Dict[str, Any]:
    """Build one tray_scenarios row from extracted label data."""
    drug = (data.get("drug_name_generic") or "").strip().lower()
    dose_val = data.get("dosage_value")
    dose_unit = (data.get("dosage_unit") or "").strip()
    patient_id = (data.get("patient_id") or "").strip() or scenario_id
    return {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "patient_id": patient_id,
        "tray_position": tray_position,
        "ordered_drug": drug,
        "ordered_dose_value": dose_val,
        "ordered_dose_unit": dose_unit,
        "tray_drug": drug,
        "tray_dose_value": dose_val,
        "tray_dose_unit": dose_unit,
        "tray_tablet_count": data.get("prescribed_tablet_count"),
        "tray_expiry_date": None,
        "expected_outcome": "DISPENSE",
        "expected_flag_code": "NONE",
        "error_description": "",
    }


def _load_json(path: Path) -> Dict[str, Any]:
    """Load a single JSON file as extraction data."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON must be an object, got {type(data)}")
    return data


def load_scenarios_from_labels_dir(labels_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Scan labels_dir for images and JSON files; build orders and trays DataFrames.

    - Images: OCR with prescription_ocr if available; otherwise skipped.
    - JSON: loaded directly (DispensingOrder-like keys).
    Each file yields one scenario (one order row, one tray row).
    """
    labels_dir = Path(labels_dir)
    if not labels_dir.is_dir():
        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    order_rows: List[Dict[str, Any]] = []
    tray_rows: List[Dict[str, Any]] = []
    use_ocr = _ocr_available()

    # Collect (scenario_id, tray_position, data) for each file
    entries: List[Tuple[str, str, Dict[str, Any]]] = []

    # JSON files
    for path in sorted(labels_dir.glob("*.json")):
        try:
            data = _load_json(path)
            scenario_id = path.stem
            entries.append((scenario_id, "A1", data))  # default tray_position
        except Exception:
            continue

    # Image files (need tray positions; use A1, A2, ... by order)
    image_paths = []
    for ext in LABEL_IMAGE_SUFFIXES:
        image_paths.extend(sorted(labels_dir.glob(f"*{ext}")))
    image_paths.sort(key=lambda p: p.name)

    for idx, path in enumerate(image_paths):
        scenario_id = path.stem
        tray_position = f"A{idx + 1}" if idx < 26 else f"A{idx // 26}{chr(65 + idx % 26)}"
        if use_ocr:
            try:
                data = _extract_from_image(path)
                entries.append((scenario_id, tray_position, data))
            except Exception:
                continue
        else:
            # No OCR: look for sidecar JSON with same stem
            sidecar = path.with_suffix(".json")
            if sidecar.exists():
                try:
                    data = _load_json(sidecar)
                    entries.append((scenario_id, tray_position, data))
                except Exception:
                    continue

    # Build rows with stable tray positions (A1, A2, ...) by order of entries
    for idx, (scenario_id, _, data) in enumerate(entries):
        tray_position = f"A{idx + 1}"
        patient_id = (data.get("patient_id") or "").strip() or scenario_id
        order_rows.append(_order_row_from_extraction(data, scenario_id))
        tray_rows.append(
            _tray_row_from_extraction(data, scenario_id, tray_position)
        )

    orders_df = pd.DataFrame(order_rows) if order_rows else pd.DataFrame()
    trays_df = pd.DataFrame(tray_rows) if tray_rows else pd.DataFrame()

    return orders_df, trays_df
