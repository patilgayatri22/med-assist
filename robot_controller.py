"""
robot_controller.py

Execution wrapper for MedAssist.

Modes:
- sim: safe local fallback
- cyberwave_twin: digital twin simulation only (no physical arm)
- cyberwave_live: real execution via robot_control.execute_pick()

Design:
- Deterministic medication rules remain the source of truth.
- Toolhouse provides summary / speech / logging.
- Robot motion only happens when rule_result["status"] == "proceed".
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import cyberwave as cw
from robot_control import execute_pick

ROBOT_MODE = os.getenv("ROBOT_MODE", "cyberwave_twin").strip().lower()

# Twin profile from your Cyberwave docs
TWIN_ID = "the-robot-studio/so101"

# Simple twin-only demo poses in joint space.
# These are NOT physical calibration values. They are only for digital-twin demo.
# Joint IDs:
# "1" shoulder_pan, "2" shoulder_lift, "3" elbow_flex,
# "4" wrist_flex, "5" wrist_roll, "6" gripper
HOME_POSE = {
    "1": 0.0,
    "2": -25.0,
    "3": 60.0,
    "4": 0.0,
    "5": 0.0,
    "6": 0.0,   # open
}

TRAY_POSES = {
    "A1": {"1": -20.0, "2": -40.0, "3": 75.0, "4": 10.0, "5": 0.0, "6": 0.0},
    "A2": {"1": -10.0, "2": -42.0, "3": 78.0, "4": 8.0,  "5": 0.0, "6": 0.0},
    "B1": {"1": 10.0,  "2": -40.0, "3": 75.0, "4": 10.0, "5": 0.0, "6": 0.0},
    "B2": {"1": 20.0,  "2": -42.0, "3": 78.0, "4": 8.0,  "5": 0.0, "6": 0.0},
}


def _default_action(status: str) -> str:
    if status == "proceed":
        return "pick_vial"
    if status == "hold":
        return "stop_and_wait"
    return "alert_human_staff"


def _get_robot_speech(
    rule_result: Dict[str, Any],
    toolhouse_output: Optional[Dict[str, Any]],
) -> str:
    if toolhouse_output and toolhouse_output.get("robot_speech"):
        return str(toolhouse_output["robot_speech"])

    if rule_result.get("speak_message"):
        return str(rule_result["speak_message"])

    status = str(rule_result.get("status", "escalate")).lower()
    if status == "proceed":
        return "Medication verified. Delivering now."
    if status == "hold":
        return "Delivery is on hold pending verification."
    return "Human assistance is required before proceeding."


def _send_joint_pose(robot: Any, pose: Dict[str, float], settle: float = 0.6) -> None:
    for joint_id, value in pose.items():
        robot.joints.set(str(joint_id), float(value))
    time.sleep(settle)


def _run_twin_pick_sequence(tray_position: str) -> Dict[str, Any]:
    """
    Digital-twin-only pick visualization.
    No physical motion. No calibration required.
    Uses simple joint-space demo poses only.
    """
    if tray_position not in TRAY_POSES:
        return {
            "success": False,
            "tray_position": tray_position,
            "flag": "FLAG_UNKNOWN_TRAY_POSITION",
            "reason": f"Tray position '{tray_position}' not defined in twin demo poses.",
        }

    robot = cw.twin(TWIN_ID)
    try:
        # Step 1: Home
        _send_joint_pose(robot, HOME_POSE, settle=0.5)

        # Step 2: Move above tray cell
        target_pose = dict(TRAY_POSES[tray_position])
        _send_joint_pose(robot, target_pose, settle=0.8)

        # Step 3: Close gripper in twin
        robot.joints.set("6", 60.0)
        time.sleep(0.6)

        # Step 4: Return home
        _send_joint_pose(robot, HOME_POSE, settle=0.8)

        return {
            "success": True,
            "tray_position": tray_position,
            "mode": "cyberwave_twin",
            "sequence": ["home", tray_position, "close_gripper", "home"],
        }
    finally:
        try:
            robot.disconnect()
        except Exception:
            pass


def execute_robot_action(
    rule_result: Dict[str, Any],
    toolhouse_output: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute MedAssist robot behavior in the configured mode.

    Expected rule_result example:
    {
        "status": "proceed",
        "action": "pick_vial",
        "reason": "all deterministic checks passed",
        "tray_position": "A1",
        ...
    }
    """
    status = str(rule_result.get("status", "escalate")).strip().lower()
    action = str(rule_result.get("action", "")).strip() or _default_action(status)
    tray_position = rule_result.get("tray_position")
    speak_message = _get_robot_speech(rule_result, toolhouse_output)

    # Hard safety gate: never move unless explicit proceed
    if status != "proceed":
        return {
            "mode": ROBOT_MODE,
            "robot_state": "BLOCKED",
            "robot_action": "no_motion",
            "allowed_to_move": False,
            "execution_result": f"BLOCKED_{status.upper()}",
            "tray_position": tray_position,
            "speak_message": speak_message,
        }

    if ROBOT_MODE == "sim":
        return {
            "mode": "sim",
            "robot_state": "EXECUTING",
            "robot_action": action,
            "allowed_to_move": True,
            "execution_result": "SIMULATED_SUCCESS",
            "tray_position": tray_position,
            "speak_message": speak_message,
        }

    if ROBOT_MODE == "cyberwave_twin":
        if not tray_position:
            return {
                "mode": "cyberwave_twin",
                "robot_state": "ERROR",
                "robot_action": action,
                "allowed_to_move": False,
                "execution_result": {
                    "success": False,
                    "flag": "FLAG_MISSING_TRAY_POSITION",
                    "reason": "Twin execution requires tray_position in the rule result.",
                },
                "tray_position": tray_position,
                "speak_message": speak_message,
            }

        twin_result = _run_twin_pick_sequence(str(tray_position))
        return {
            "mode": "cyberwave_twin",
            "robot_state": "EXECUTING" if twin_result.get("success") else "ERROR",
            "robot_action": action,
            "allowed_to_move": bool(twin_result.get("success")),
            "execution_result": twin_result,
            "tray_position": tray_position,
            "speak_message": speak_message,
        }

    if ROBOT_MODE == "cyberwave_live":
        if not tray_position:
            return {
                "mode": "cyberwave_live",
                "robot_state": "ERROR",
                "robot_action": action,
                "allowed_to_move": False,
                "execution_result": {
                    "success": False,
                    "flag": "FLAG_MISSING_TRAY_POSITION",
                    "reason": "Live execution requires tray_position in the rule result.",
                },
                "tray_position": tray_position,
                "speak_message": speak_message,
            }

        pick_result = execute_pick(str(tray_position))
        return {
            "mode": "cyberwave_live",
            "robot_state": "EXECUTING" if pick_result.get("success") else "ERROR",
            "robot_action": action,
            "allowed_to_move": bool(pick_result.get("success")),
            "execution_result": pick_result,
            "tray_position": tray_position,
            "speak_message": speak_message,
        }

    raise ValueError(
        f"Unsupported ROBOT_MODE: {ROBOT_MODE}. "
        "Use sim, cyberwave_twin, or cyberwave_live."
    )
