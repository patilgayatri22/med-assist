from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from llm_toolhouse_client import summarize_rule_result
from medication_rules import evaluate_scenario


class MedAssistRunner:
    def __init__(self, data_dir: Optional[str] = None) -> None:
        root = Path(data_dir or Path(__file__).parent)
        self.orders = pd.read_csv(root / "patient_medication_orders.csv")
        self.trays = pd.read_csv(root / "tray_scenarios.csv")

    def get_order(self, patient_id: str) -> Dict[str, Any]:
        row = self.orders.loc[self.orders["patient_id"] == patient_id]
        if row.empty:
            raise KeyError(f"No patient order found for {patient_id}")
        return row.iloc[0].to_dict()

    def get_scenario(self, scenario_id: str) -> Dict[str, Any]:
        row = self.trays.loc[self.trays["scenario_id"] == scenario_id]
        if row.empty:
            raise KeyError(f"No tray scenario found for {scenario_id}")
        return row.iloc[0].to_dict()

    def run_by_scenario_id(self, scenario_id: str, include_llm_summary: bool = True) -> Dict[str, Any]:
        tray = self.get_scenario(scenario_id)
        order = self.get_order(tray["patient_id"])
        rule_result = evaluate_scenario(order, tray)

        prompt = f"""
Patient order:
{order}

Tray vision payload:
{tray}

Deterministic rule-engine output:
{rule_result}

Explain the robot action without overriding the rule-engine result.
""".strip()

        llm_summary = summarize_rule_result(prompt, rule_result) if include_llm_summary else None

        return {
            "scenario_id": tray["scenario_id"],
            "scenario_type": tray["scenario_type"],
            "patient_id": tray["patient_id"],
            "tray_position": tray["tray_position"],
            "expected_outcome": tray["expected_outcome"],
            "expected_flag_code": tray["expected_flag_code"],
            "rule_result": rule_result,
            "llm_summary": llm_summary,
            "matches_expected": (
                rule_result["action"] == "dispense"
                and tray["expected_outcome"] == "DISPENSE"
                or rule_result["flag_code"] == tray["expected_flag_code"]
            ),
        }

    def run_all(self, include_llm_summary: bool = False) -> pd.DataFrame:
        rows = []
        for scenario_id in self.trays["scenario_id"].tolist():
            result = self.run_by_scenario_id(scenario_id, include_llm_summary=include_llm_summary)
            rule = result["rule_result"]
            rows.append(
                {
                    "scenario_id": result["scenario_id"],
                    "scenario_type": result["scenario_type"],
                    "expected_outcome": result["expected_outcome"],
                    "expected_flag_code": result["expected_flag_code"],
                    "actual_status": rule["status"],
                    "actual_action": rule["action"],
                    "actual_flag_code": rule["flag_code"],
                    "matches_expected": result["matches_expected"],
                }
            )
        return pd.DataFrame(rows)
