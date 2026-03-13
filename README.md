# MedAssist Agent

This version aligns the rule engine to the current MedAssist decision sequence:

1. Allergy
2. Already dispensed
3. Overdue
4. Wrong patient / tray assignment
5. LASA confusion
6. Drug match
7. Out-of-range ordered dose
8. Dose match
9. Expiry
10. Tablet count
11. High-alert verification
12. Dispense / pick command

The arm only receives a pick command on an explicit all-clear.

## Files

- `medication_rules.py` - deterministic safety engine
- `agent_runner.py` - loads CSV data and executes scenarios
- `llm_toolhouse_client.py` - optional Featherless + Toolhouse summary layer
- `test_scenarios.py` - validates expected flags across the scenario CSV
- `main.py` - CLI

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- add `FEATHERLESS_API_KEY`
- add rotated `TOOLHOUSE_API_KEY` if you want tool use
- set `ENABLE_LLM_SUMMARY=true` only after keys are configured

## Run

```bash
python3 test_scenarios.py
python3 main.py
```

Inside the CLI:
- `list`
- `test`
- `scenario SCN-015`
