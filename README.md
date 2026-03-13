# MedAssist AI

AI-powered medication safety verification system built during the Robotic Agents Hackathon.

## Features

- Medication safety verification with deterministic rule engine
- LLM reasoning using Featherless AI
- Toolhouse agent orchestration
- CSV-based patient medication orders
- Interactive CLI interface
- 10+ medical scenario simulation

## Rule Engine Decision Sequence

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

## Tech Stack

- Python
- Toolhouse
- Featherless AI
- Supabase (optional)
- FastAPI (optional)

## Files

- `medication_rules.py` - deterministic safety engine
- `agent_runner.py` - loads CSV data and executes scenarios
- `llm_toolhouse_client.py` - optional Featherless + Toolhouse summary layer
- `llm_client.py` - LLM integration with JSON parsing
- `test_scenarios.py` - validates expected flags across the scenario CSV
- `main.py` - Interactive CLI interface
- `robot_controller.py` - Robot control logic
- `prompts.py` - Medical prompts and instructions

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- add `FEATHERLESS_API_KEY`
- add `TOOLHOUSE_API_KEY` if you want tool use
- set `ROBOT_MODE=cyberwave_twin`

## Run

```bash
python3 test_scenarios.py
python3 main.py
```

Inside the CLI:
- `list` - List available scenarios
- `test` - Run test scenarios
- `scenario SCN-015` - Run specific scenario
- Interactive modes: Basic, Toolhouse, Scenario Testing
