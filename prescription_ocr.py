#!/usr/bin/env python3
"""
Dispensing label OCR — extracts structured fields from hospital dispensing label
images using EasyOCR (raw text) + llama3.2-vision via Ollama (structured extraction).

Usage:
    python prescription_ocr.py process <image> [<image> ...]
    python prescription_ocr.py list [--limit N]
    python prescription_ocr.py show <id>
    python prescription_ocr.py eval <annotations.json> <labels_dir>

Requirements:
    pip install easyocr ollama
    ollama pull llama3.2-vision
"""

import argparse
import base64
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Use certifi CA bundle so HTTPS works on macOS (avoids SSL: CERTIFICATE_VERIFY_FAILED)
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except Exception:
    pass

import easyocr
import ollama
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Structured extraction schema — matches hospital dispensing label format
# ---------------------------------------------------------------------------

class DispensingOrder(BaseModel):
    """Structured fields extracted from a hospital dispensing label."""

    # Patient
    patient_id: Optional[str] = Field(None, description="Patient ID (e.g. PT-00101)")
    patient_name: Optional[str] = Field(None, description="Full name of the patient")
    dob: Optional[str] = Field(None, description="Date of birth (YYYY-MM-DD)")
    room_number: Optional[str] = Field(None, description="Hospital room number (e.g. 3A-01)")

    # Medication
    drug_name_generic: Optional[str] = Field(None, description="Generic drug name (lowercase)")
    drug_name_brand: Optional[str] = Field(None, description="Brand/trade name of the drug")
    dosage_value: Optional[str] = Field(None, description="Numeric dosage amount (e.g. '500')")
    dosage_unit: Optional[str] = Field(None, description="Dosage unit (e.g. 'mg', 'mL', 'units')")
    route: Optional[str] = Field(None, description="Route of administration (e.g. oral, IV, subcutaneous)")
    frequency: Optional[str] = Field(None, description="Dosing frequency (e.g. 'twice daily', 'once daily')")
    scheduled_time: Optional[str] = Field(None, description="Scheduled administration time (HH:MM 24h)")
    prescribed_tablet_count: Optional[str] = Field(None, description="Number of tablets/doses dispensed")

    # Safety flags
    high_alert: Optional[str] = Field(None, description="'True' if high-alert medication, else 'False'")
    lasa_risk: Optional[str] = Field(None, description="'True' if LASA (look-alike/sound-alike) risk, else 'False'")
    lasa_pair: Optional[str] = Field(None, description="Name of the LASA pair drug if applicable")

    # Clinical
    allergies: Optional[str] = Field(None, description="Known patient allergies listed on label")
    special_instructions: Optional[str] = Field(None, description="Special administration instructions")
    dispensing_status: Optional[str] = Field(None, description="Status: pending, dispensed, verified, etc.")

    # Prescriber
    prescriber: Optional[str] = Field(None, description="Prescribing physician name (e.g. Dr. Chen)")

    # Meta
    confidence_notes: Optional[str] = Field(
        None,
        description="Fields that were unclear or partially legible — note them here",
    )


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS dispensing_orders (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    source_image            TEXT,
    extracted_at            TEXT NOT NULL,

    patient_id              TEXT,
    patient_name            TEXT,
    dob                     TEXT,
    room_number             TEXT,

    drug_name_generic       TEXT,
    drug_name_brand         TEXT,
    dosage_value            TEXT,
    dosage_unit             TEXT,
    route                   TEXT,
    frequency               TEXT,
    scheduled_time          TEXT,
    prescribed_tablet_count TEXT,

    high_alert              TEXT,
    lasa_risk               TEXT,
    lasa_pair               TEXT,

    allergies               TEXT,
    special_instructions    TEXT,
    dispensing_status       TEXT,

    prescriber              TEXT,
    confidence_notes        TEXT,
    raw_json                TEXT
);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(DB_SCHEMA)
    conn.commit()
    return conn


def insert_order(
    conn: sqlite3.Connection,
    order: DispensingOrder,
    source_image: str,
) -> int:
    data = order.model_dump()
    now = datetime.utcnow().isoformat()
    conn.execute(
        """
        INSERT INTO dispensing_orders (
            source_image, extracted_at,
            patient_id, patient_name, dob, room_number,
            drug_name_generic, drug_name_brand, dosage_value, dosage_unit,
            route, frequency, scheduled_time, prescribed_tablet_count,
            high_alert, lasa_risk, lasa_pair,
            allergies, special_instructions, dispensing_status,
            prescriber, confidence_notes, raw_json
        ) VALUES (
            :source_image, :extracted_at,
            :patient_id, :patient_name, :dob, :room_number,
            :drug_name_generic, :drug_name_brand, :dosage_value, :dosage_unit,
            :route, :frequency, :scheduled_time, :prescribed_tablet_count,
            :high_alert, :lasa_risk, :lasa_pair,
            :allergies, :special_instructions, :dispensing_status,
            :prescriber, :confidence_notes, :raw_json
        )
        """,
        {
            **data,
            "source_image": source_image,
            "extracted_at": now,
            "raw_json": json.dumps(data),
        },
    )
    conn.commit()
    row_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return row_id


# ---------------------------------------------------------------------------
# OCR extraction
# ---------------------------------------------------------------------------

# Shared EasyOCR reader (lazy-loaded once per process; not re-downloaded per request)
_ocr_reader: Optional[easyocr.Reader] = None


def get_ocr_reader() -> easyocr.Reader:
    global _ocr_reader
    if _ocr_reader is None:
        print("  [EasyOCR] Loading model (first run only)…", flush=True)
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
    return _ocr_reader


def extract_raw_text(image_path: Path) -> str:
    """Run EasyOCR on the image and return all detected text as a single string."""
    reader = get_ocr_reader()
    results = reader.readtext(str(image_path), detail=0, paragraph=True)
    return "\n".join(results)


def load_image_as_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


EXTRACTION_PROMPT = """You are a hospital pharmacy data specialist. Extract structured information from this dispensing label.

OCR text already extracted from the image (use as a hint):
{ocr_text}

Rules:
- Extract every visible field. Leave fields null only if absent or completely illegible.
- high_alert and lasa_risk must be the string "True" or "False".
- dob must be YYYY-MM-DD format.
- scheduled_time must be HH:MM in 24-hour format.
- Do not invent values not visible on the label.
- If a field is partially legible, include what you can and note it in confidence_notes.

Return ONLY a valid JSON object with these exact fields (no markdown, no explanation):
{{
  "patient_id": null,
  "patient_name": null,
  "dob": null,
  "room_number": null,
  "drug_name_generic": null,
  "drug_name_brand": null,
  "dosage_value": null,
  "dosage_unit": null,
  "route": null,
  "frequency": null,
  "scheduled_time": null,
  "prescribed_tablet_count": null,
  "high_alert": null,
  "lasa_risk": null,
  "lasa_pair": null,
  "allergies": null,
  "special_instructions": null,
  "dispensing_status": null,
  "prescriber": null,
  "confidence_notes": null
}}"""


def extract_label(image_path: Path) -> DispensingOrder:
    # Step 1: EasyOCR for raw text
    raw_text = extract_raw_text(image_path)

    # Step 2: llama3.2-vision for structured extraction
    image_b64 = load_image_as_base64(image_path)
    prompt = EXTRACTION_PROMPT.format(ocr_text=raw_text or "(no text detected)")

    response = ollama.chat(
        model="llama3.2-vision",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_b64],
            }
        ],
        options={"temperature": 0},
    )

    content = response["message"]["content"].strip()

    # Extract just the JSON object (ignore any surrounding markdown/text)
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model response:\n{content}")
    content = match.group(0)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model returned invalid JSON: {exc}\nRaw response:\n{content}") from exc

    # Coerce all values to str (model sometimes returns int/bool instead of str)
    coerced = {k: (str(v) if v is not None else None) for k, v in data.items()}
    return DispensingOrder(**coerced)


# ---------------------------------------------------------------------------
# Evaluation against ground-truth annotations
# ---------------------------------------------------------------------------

EVAL_FIELDS = [
    "patient_id", "patient_name", "dob", "room_number",
    "drug_name_generic", "drug_name_brand", "dosage_value", "dosage_unit",
    "route", "frequency", "scheduled_time", "prescribed_tablet_count",
    "high_alert", "lasa_risk", "lasa_pair",
    "allergies", "special_instructions", "dispensing_status", "prescriber",
]


def normalize(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def score_extraction(extracted: DispensingOrder, ground_truth: dict) -> dict:
    results = {}
    for field in EVAL_FIELDS:
        gt_val = normalize(ground_truth.get(field, ""))
        ex_val = normalize(getattr(extracted, field, None))
        results[field] = {
            "match": gt_val == ex_val,
            "expected": gt_val,
            "got": ex_val,
        }
    return results


def cmd_eval(args: argparse.Namespace) -> None:
    annotations_path = Path(args.annotations)
    labels_dir = Path(args.labels_dir)

    with open(annotations_path) as f:
        annotations = {item["filename"]: item for item in json.load(f)["labels"]}

    conn = get_connection(args.db)

    total_fields = 0
    correct_fields = 0
    file_results = []

    images = sorted(labels_dir.glob("*.png")) + sorted(labels_dir.glob("*.jpg"))
    images = [img for img in images if img.name in annotations]

    print(f"Evaluating {len(images)} labelled images…\n")

    for image_path in images:
        gt = annotations[image_path.name]
        print(f"  {image_path.name} … ", end="", flush=True)

        try:
            order = extract_label(image_path)
            insert_order(conn, order, str(image_path.resolve()))
            field_scores = score_extraction(order, gt)

            n_correct = sum(1 for v in field_scores.values() if v["match"])
            n_total = len(field_scores)
            correct_fields += n_correct
            total_fields += n_total

            pct = n_correct / n_total * 100
            print(f"{n_correct}/{n_total} fields ({pct:.0f}%)")

            for field, result in field_scores.items():
                if not result["match"]:
                    print(f"    x {field:<28} expected={result['expected']!r:30} got={result['got']!r}")

            file_results.append({
                "file": image_path.name,
                "correct": n_correct,
                "total": n_total,
                "pct": pct,
            })

        except Exception as exc:
            print(f"ERROR — {exc}", file=sys.stderr)

    conn.close()

    if total_fields > 0:
        overall_pct = correct_fields / total_fields * 100
        print(f"\n{'='*60}")
        print(f"OVERALL ACCURACY: {correct_fields}/{total_fields} fields = {overall_pct:.1f}%")
        print(f"{'='*60}")

        worst = sorted(file_results, key=lambda x: x["pct"])
        print("\nLowest-scoring images:")
        for r in worst[:5]:
            print(f"  {r['file']:<40} {r['correct']}/{r['total']} ({r['pct']:.0f}%)")


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def cmd_process(args: argparse.Namespace) -> None:
    conn = get_connection(args.db)

    for image_path_str in args.images:
        image_path = Path(image_path_str)
        if not image_path.exists():
            print(f"[SKIP] File not found: {image_path}", file=sys.stderr)
            continue

        print(f"Processing: {image_path.name} …", end=" ", flush=True)
        try:
            order = extract_label(image_path)
            row_id = insert_order(conn, order, str(image_path.resolve()))
            print(f"OK → row {row_id}")
            print(f"  Patient   : {order.patient_name or 'N/A'} ({order.patient_id or 'N/A'}) Room {order.room_number or 'N/A'}")
            print(f"  Medication: {order.drug_name_generic or 'N/A'} ({order.drug_name_brand or 'N/A'}) {order.dosage_value or ''}{order.dosage_unit or ''}")
            print(f"  Frequency : {order.frequency or 'N/A'} @ {order.scheduled_time or 'N/A'}")
            print(f"  Prescriber: {order.prescriber or 'N/A'}")
            flags = []
            if order.high_alert == "True":
                flags.append("HIGH ALERT")
            if order.lasa_risk == "True":
                flags.append(f"LASA ({order.lasa_pair})")
            if flags:
                print(f"  Flags     : {', '.join(flags)}")
            if order.confidence_notes:
                print(f"  Notes     : {order.confidence_notes}")
            print()
        except Exception as exc:
            print(f"ERROR — {exc}", file=sys.stderr)

    conn.close()


def cmd_list(args: argparse.Namespace) -> None:
    conn = get_connection(args.db)
    rows = conn.execute(
        """
        SELECT id, extracted_at, patient_name, patient_id, drug_name_generic,
               dosage_value, dosage_unit, room_number
        FROM dispensing_orders ORDER BY id DESC LIMIT ?
        """,
        (args.limit,),
    ).fetchall()

    if not rows:
        print("No orders found.")
        return

    print(f"{'ID':<5} {'Patient':<22} {'PID':<10} {'Room':<8} {'Drug':<25} {'Dose'}")
    print("-" * 90)
    for r in rows:
        dose = f"{r['dosage_value'] or ''}{r['dosage_unit'] or ''}".strip()
        print(
            f"{r['id']:<5} {(r['patient_name'] or 'N/A'):<22} "
            f"{(r['patient_id'] or 'N/A'):<10} {(r['room_number'] or 'N/A'):<8} "
            f"{(r['drug_name_generic'] or 'N/A'):<25} {dose}"
        )
    conn.close()


def cmd_show(args: argparse.Namespace) -> None:
    conn = get_connection(args.db)
    row = conn.execute(
        "SELECT * FROM dispensing_orders WHERE id = ?", (args.order_id,)
    ).fetchone()
    if row is None:
        print(f"Order {args.order_id} not found.")
        return
    data = json.loads(row["raw_json"])
    print(f"\n=== Order #{row['id']} — {row['extracted_at']} ===")
    print(f"Source: {row['source_image']}\n")
    for field, value in data.items():
        if value is not None:
            print(f"  {field:<28}: {value}")
    conn.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hospital dispensing label OCR — extract and store structured order data",
    )
    parser.add_argument("--db", default="dispensing_orders.db")

    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("process", help="OCR one or more label images")
    p.add_argument("images", nargs="+")
    p.set_defaults(func=cmd_process)

    p = sub.add_parser("list", help="List stored orders")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="Show full details for one order")
    p.add_argument("order_id", type=int)
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("eval", help="Run OCR on all labelled images and score accuracy")
    p.add_argument("annotations", help="Path to annotations.json")
    p.add_argument("labels_dir", help="Directory containing label images")
    p.set_defaults(func=cmd_eval)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
