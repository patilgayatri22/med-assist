
"""
toolhouse_adapter.py

Helpers for integrating your friend's Toolhouse agent output.
"""

from __future__ import annotations

from typing import Any, Dict


def build_toolhouse_payload(
    scenario_id: int,
    order: Dict[str, Any],
    tray: Dict[str, Any],
    rule_result: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "status": rule_result.get("status"),
        "action": rule_result.get("action"),
        "reason": rule_result.get("reason"),
        "required_checks": rule_result.get("required_checks", []),
        "speak_message": rule_result.get("speak_message"),
        "tray_position": rule_result.get("tray_position"),
        "order": order,
        "tray": tray,
        "rule_result": rule_result,
    }


def normalize_toolhouse_output(toolhouse_output: Dict[str, Any], rule_result: Dict[str, Any]) -> Dict[str, Any]:
    output = dict(toolhouse_output or {})
    log_entry = dict(output.get("log_entry") or {})

    if log_entry.get("decision") is None:
        log_entry["decision"] = rule_result.get("status")

    if log_entry.get("reason") is None:
        log_entry["reason"] = rule_result.get("reason")

    output["log_entry"] = log_entry
    return output
