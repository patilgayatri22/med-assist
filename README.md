# MedAssist — AI-Powered Medication Verification & Dispensing Agent

> **Robotic Agents Hackathon · Track: Cyberwave × Toolhouse**
> Built by Aaryan Mahipal, Sagar Patel, Anna Saltveit & Gayatri Patil · March 2026

MedAssist is a robotic dispensing agent that takes the human hand out of the highest-error moment in medication delivery. It closes the full **sense → reason → act** loop: a camera sees what's on the tray, an AI agent reasons about what *should* be there for a specific patient, and a robotic arm physically executes the verified pick — or refuses to move if anything is wrong.

---

## The Problem

Approximately **1.5 million people** are harmed by medication errors in the US each year, costing the healthcare system an estimated **$3.5 billion annually**. Nurses and pharmacists in high-pressure ward environments dispense medications manually — often across dozens of patients per shift — with no automated verification between picking a vial and administering it. A misread label, a distraction, or a shelf stocked in the wrong order is all it takes.

Existing solutions (barcode scanners, electronic medication administration records) catch some errors but still depend on a human physically verifying the right item at the right time.

> **The gap MedAssist fills:** There is no commercially deployed system that autonomously closes the loop — sees what medication is present, reasons about what should be dispensed for a specific patient, and physically acts on that decision without a human in the picking step.

---

## How It Works

MedAssist runs a complete **Sense → Reason → Act** loop on every dispense event.

```
Patient Record + Vision Payload
         │
         ▼
  ┌──────────────────┐
  │  Toolhouse Agent │  ← runs 10-check decision sequence
  │  (Claude Vision) │
  └──────┬───────────┘
         │ DISPENSE or HALT + alert
         ▼
  ┌──────────────────┐     ┌──────────────────┐
  │  SO-101 Arm Pick │────►│  ElevenLabs Voice │
  │  (Cyberwave)     │     │  Narration        │
  └──────────────────┘     └──────────────────┘
         │
         ▼
  Dispense event logged → Ready for next patient
```

### Sense
The SO-101 robotic arm's camera scans the medication tray in real time. A vision model (Claude) identifies each vial — drug name, dosage, expiry, tray position — and returns a structured payload.

### Reason
A Toolhouse agent receives the vision payload alongside the patient medication record. It runs a 10-check safety sequence in strict priority order. The arm only moves on an explicit all-clear.

### Act
The agent calls the Cyberwave robot skill as a tool: `pick(position="B2")`. The SO-101 arm moves to the verified position, grips, and lifts the vial. ElevenLabs narrates the action in real time.

### Loop
The grip sensor confirms the pick. The agent logs the dispense event. The system is ready for the next patient.

---

## Agent Decision Sequence

The agent receives two inputs simultaneously: the **patient medication record** and the **vision payload** from the arm camera. Checks run in strict priority order — **the first failure halts the process immediately**. No lower-priority checks are evaluated after a failure fires.

| # | Check | Condition | On Failure |
|---|-------|-----------|------------|
| 1 | **Allergy** | Tray drug matches a documented patient allergen or cross-reactive drug class (e.g. penicillin allergy + amoxicillin on tray) | `FLAG_ALLERGY` — halt immediately. Alert names allergen and drug. Contacts prescriber. No exceptions. |
| 2 | **Already Dispensed** | `dispensing_status` field equals `dispensed` for this order | `FLAG_ALREADY_DISPENSED` — halt. Alert includes time of previous dose. Prevents double-dosing. |
| 3 | **LASA Confusion** | Tray drug is a known look-alike/sound-alike of the ordered drug (matched against `lasa_pair` field) | `FLAG_LASA` — halt. Alert explicitly names both drugs. Generic wrong-drug message is insufficient for LASA pairs. |
| 4 | **Drug Match** | Tray drug name does not match ordered drug name (case-insensitive generic name comparison) | `FLAG_WRONG_DRUG` — halt. Alert states what was ordered and what was found. |
| 5 | **Out of Range** | Ordered dose falls outside therapeutic range defined in the medication library | `FLAG_OUT_OF_RANGE` — halt. Flags a potential prescribing error. Agent is the last safety net. |
| 6 | **Dose Match** | Tray dose value or unit does not match ordered dose | `FLAG_WRONG_DOSE` (`DOSE_LOW` or `DOSE_HIGH`) — halt. Critical for narrow-window drugs like warfarin. |
| 7 | **Expiry Check** | Vial expiry date (read from label by vision model) is earlier than today's date | `FLAG_EXPIRED` — halt. Nurse instructed to remove vial and notify pharmacy. |
| 8 | **Tablet Count** | Tablet count on vial label does not match prescribed count in patient order | `FLAG_TABLET_COUNT` — halt. Flags partial fills and potential batch-vial mix-ups for pharmacist review. |
| 9 | **High Alert** | Drug is on the ISMP high-alert list (`high_alert = true`) and all prior checks passed | `FLAG_HIGH_ALERT_VERIFY` — arm **pauses**. Requires secondary confirmation signal. Does NOT auto-dispense. |
| 10 | **All Clear** | All nine checks passed with no flags | `DISPENSE` — agent issues pick command to SO-101 arm. |

> **Key principle:** Each check is a hard stop. A correct drug/dose match cannot override an allergy flag. A high-alert drug cannot slip through without verification. **Silence is never treated as approval — the arm only moves on an explicit `DISPENSE` signal.**

---

## Pick Mechanism — SO-101 Arm

Once the agent issues a `DISPENSE` signal, the SO-101 arm executes the pick.

**Position mapping:** Each tray cell (A1, A2, B1, …) maps to a pre-calibrated `(x, y, z)` coordinate in the arm's joint space. This grid is defined once at hardware setup and stored in the joint map reference file. The arm looks up the coordinate dictionary — it does not recalculate position at runtime.

**Arm movement sequence:**
```
Move to above-cell position (safe height)
  → Descend to vial height
  → Close gripper
  → Lift
  → Return to neutral handoff position (nurse receives vial)
```

**Grip confirmation:** After the gripper closes, a current threshold on the STS3215 servo is read. Higher draw = vial gripped. If current stays low (empty grasp), the agent logs `FLAG_PICK_FAILED` and narrates the error — it does not return to home silently with an empty hand.

**Handoff:** There is no automated place step. The arm returns to a fixed handoff position and a nurse takes the vial. This is intentional — final patient administration requires a human in the loop.

---

## Hardware Integration — Known Limitations

The SO-101 arm experienced hardware issues during the hackathon that prevented us from testing the physical integration at all. As a result, the end-to-end code path from Toolhouse agent decision to arm pick command was not testable — the sense → reason pipeline (camera, vision model, agent decision logic) ran as designed, but the Cyberwave robot skill integration could not be validated against real hardware.

The demo reflects what we were able to verify: the agent correctly identifies medications, runs the full 10-check sequence, and issues the right `DISPENSE` or `HALT` signal. The physical arm movement shown is not live agent-dispatched.

---

## Demo Sequence

The full demo run is under 3 minutes, six stages, with clear outcomes at each step.

| # | Stage | What happens | What the judge sees |
|---|-------|-------------|---------------------|
| 01 | **Scene set** | A tray holds 4–5 labelled medication vials. A patient card reads: "Patient: J. Rivera — 10mg Metformin, morning dose." The SO-101 arm is at rest. | Setup understood in under 10 seconds. |
| 02 | **Sense** | The camera activates. Vision model scans the tray, identifies each vial and position. Data is passed as a structured payload to the Toolhouse agent. | Live readout: "Detected: Metformin 10mg (pos B2), Lisinopril 5mg (pos A1), Atorvastatin 20mg (pos C3)…" |
| 03 | **Reason** | Agent receives vision payload + patient record. Runs check sequence. Decision: PROCEED. | Agent log: "Patient J. Rivera → Metformin 10mg → Match confirmed → Dispatching arm." |
| 04 | **Act** | Agent calls `pick(position="B2")`. SO-101 arm moves to vial B2, grips, lifts. ElevenLabs voice: *"Metformin 10mg confirmed for patient Rivera. Dispensing now."* | Physical pick + simultaneous voice narration. |
| 05 | **⚠ Error demo** | Tray reset with WRONG vial at B2 (Lisinopril where Metformin should be). Agent re-runs. Vision detects mismatch. Decision: HOLD. Arm stays still. Voice: *"Mismatch detected. Expected Metformin 10mg. Found Lisinopril 5mg. Alerting staff."* | **The robot says no.** Most teams show their robot doing the right thing when everything is correct. We show our agent catching the wrong thing before the robot ever moves. |
| 06 | **Recovery** | Correct vial returned to B2. Agent re-verifies. Arm picks. Voice confirms. Loop closes. | Full end-to-end success on screen and in the physical world. |

---

## Tech Stack

| Tool | Role | Why |
|------|------|-----|
| **Cyberwave / SO-101** | Physical execution layer | Provides the arm platform and robot skill APIs. Workflow-based control lets the agent call robot skills as structured tools. |
| **Toolhouse** | Agent reasoning brain | Orchestrates all tool calls — vision output in, patient record check, decision logic, robot skill dispatch out. Enables a true agentic loop rather than scripted if/else control. |
| **OCR + Ollama Vision** | Vial label OCR & parsing | Reads drug name, dosage, expiry date, and tray position from the physical label. Returns a structured payload to the Toolhouse agent. |
| **smallest.ai** | Real-time voice narration | Narrates every agent decision as it happens. Transforms a silent robot into a communicative clinical assistant. |
| **Jade Hosting** | Agent API hosting | Hosts the agent endpoint reliably on shared hackathon Wi-Fi. Removes the single biggest live demo failure risk: local server going down mid-demo. |
| **SQLite** | Dispense event logging | `dispensing_orders.db` stores all dispense and halt events with timestamps for the audit trail. |
| **React + TypeScript** | Frontend framework | Component-based architecture with full type safety across the dashboard and agent log UI. |
| **Tailwind CSS** | Frontend styling | Utility-first styling for rapid UI development; consistent design system across the live agent log, check sequence display, and dispense event history. |

### Why Cyberwave × Toolhouse together

Neither platform alone is sufficient. Cyberwave without Toolhouse gives us a programmable arm but no reasoning layer. Toolhouse without Cyberwave gives us an intelligent agent with no physical reach. Together, they enable the full sense → reason → act loop that defines a true robotic agent.

---

## Synthetic Data Generation

Real pharmacy dispensing labels contain protected health information (PHI) and are not publicly available for model training. To develop and evaluate the vision model's label-parsing capabilities, we generated a synthetic dataset of realistic inpatient dispensing label images from scratch.

### Generation Approach

We defined a **medication order schema** with 19 fields covering patient identity, drug details, dosage, scheduling, and safety flags. Realistic values for each field were drawn from curated reference lists:

- **Drug names** sourced from a curated list of commonly dispensed inpatient medications (generic + brand pairs), including ISMP high-alert drugs and known LASA pairs
- **Patient demographics** (name, DOB, room number) generated using `faker` to produce realistic but entirely fictitious records
- **Dosage values** sampled within clinically plausible therapeutic ranges per drug, with intentional out-of-range outliers seeded for model robustness testing
- **Dispensing status** (`pending` / `dispensed` / `overdue`) and safety flags (`high_alert`, `lasa_risk`) assigned probabilistically to reflect realistic ward distributions
- **Expiry dates** generated with a small percentage of already-expired vials to test the expiry check

### Label Rendering

Each medication order record was rendered into a label image using a Python script (`prescription_ocr.py`) that:

1. Lays out all fields into a standardised pharmacy label template (mimicking real inpatient label formats)
2. Applies colour-coded badges for dispensing status (green/amber/red), high-alert flags (red), and LASA flags (orange)
3. Adds controlled visual noise — slight rotation, print blur, uneven lighting gradients — to simulate real label scan conditions
4. Renders at multiple resolutions to test OCR robustness across camera distances

### Ground Truth & Annotations

Every generated image is paired with a structured JSON entry in `dispensing_labels/annotations.json`, containing the exact field values used to render that label. This provides ground-truth annotations for:

- OCR accuracy evaluation (does the vision model read the drug name correctly?)
- Field extraction completeness (are all 19 fields parsed?)
- Edge case coverage (LASA pairs, expired vials, high-alert drugs, out-of-range doses)

### Dataset Composition

The dataset was intentionally skewed toward edge cases to stress-test the safety checks:

| Category | Share of dataset |
|----------|-----------------|
| Standard dispense (all checks pass) | ~40% |
| Wrong drug / LASA confusion scenarios | ~15% |
| Expired vials | ~10% |
| Incorrect tablet counts / partial fills | ~10% |
| High-alert drugs | ~10% |
| Allergy conflicts | ~8% |
| Already-dispensed / double-dose scenarios | ~7% |

All images are fully synthetic. No real patient data was used at any stage of generation or testing.

---

## Repository Structure

```
med-assist/
├── backend/                  # Python agent + API server
├── frontend/                 # TypeScript dashboard (live agent log & status)
├── dispensing_labels/        # Synthetic training label images + annotations.json
├── prescription_ocr.py       # Vision label parser (Claude Vision wrapper)
├── dispensing_orders.db      # SQLite dispense event log
└── .gitignore
```

**Languages:** Python 54% · TypeScript 43% · Other 3%

---

## Setup & Running Locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- SO-101 arm calibrated and connected
- Toolhouse API key
- smallest.ai API key
- Jade hosting endpoint configured

### 1. Hardware Setup (required before any live run)

```bash
# Fix the tray at a consistent position relative to the arm base
# Measure (x, y, z) for each tray cell (A1, A2, B1, ...)

# Run arm calibration across all 6 joints
lerobot-calibrate --all-joints

# Store calibration profile and grid coordinates
# Output must be saved to: references/so101/
# before any live run
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt

export TOOLHOUSE_API_KEY=your_key
export ELEVENLABS_API_KEY=your_key
export JADE_ENDPOINT=your_endpoint

python main.py
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Dashboard runs at http://localhost:3000
```

The dashboard displays the live agent decision log, check sequence results per patient, and the full dispense event history from `dispensing_orders.db`.

---

## Data — Synthetic Dispensing Label Dataset

The `dispensing_labels/` directory contains a synthetic dataset of **pharmacy dispensing label images** generated from realistic inpatient patient records. These were used to develop and test the vision model's label-parsing capabilities.

Each label image renders all 19 fields from the patient medication order schema:

| Field | Description |
|-------|-------------|
| `patient_id`, `patient_name`, `dob`, `room_number` | Patient identity |
| `drug_name_generic`, `drug_name_brand` | Generic + brand drug name |
| `dosage_value`, `dosage_unit`, `route`, `frequency` | Dosage and administration |
| `scheduled_time`, `prescribed_tablet_count` | Scheduling + quantity |
| `dispensing_status` | `pending` / `dispensed` / `overdue` (colour-coded badge) |
| `high_alert` | ISMP high-alert flag (red badge) |
| `lasa_risk`, `lasa_pair` | Look-alike/sound-alike flag + pair name (orange badge) |
| `allergies` | Patient allergen flags (red warning block) |
| `special_instructions` | Free-text clinical notes |
| `prescriber` | Prescribing physician |

`dispensing_labels/annotations.json` provides ground-truth field annotations for every image in the dataset, suitable for OCR model training and evaluation.

> **Note on real data:** Real pharmacy dispensing labels contain PHI and are not publicly available. All images in this dataset are synthetically generated — no real patient data is used.

---

## Safety Design Principles

- **Fail closed, not open.** Every ambiguity halts the arm. The agent never defaults to dispensing.
- **Priority order is immutable.** An allergy flag cannot be overridden by a drug match. The sequence runs top-to-bottom, every time.
- **Silence is not approval.** The arm moves only on an explicit `DISPENSE` signal from the agent.
- **Human in the loop for administration.** The arm returns the vial to a handoff position. A nurse completes administration. MedAssist is a verification and dispensing aid — not an autonomous medication administrator.
- **High-alert drugs always pause.** Even a perfect match on a high-alert drug requires a secondary confirmation signal. The arm never auto-dispenses these.

---

*MedAssist · Robotic Agents Hackathon · March 2026*
