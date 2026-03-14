def evaluate(order, tray):
    """Legacy: returns (status, reason). Prefer evaluate_scenario for full check sequence."""
    if tray.get("expired", False):
        return "hold", "expired medication"
    order_drug = order.get("drug") or order.get("drug_name_generic") or order.get("ordered_drug")
    order_dose = order.get("dose") or _dose_str(order, "dosage_value", "dosage_unit") or _dose_str(order, "ordered_dose_value", "ordered_dose_unit")
    tray_drug = tray.get("drug") or tray.get("tray_drug") or tray.get("ordered_drug")
    tray_dose = tray.get("dose") or _dose_str(tray, "tray_dose_value", "tray_dose_unit")
    if order_drug != tray_drug:
        return "hold", "drug mismatch"
    if order_dose != tray_dose:
        return "hold", "dose mismatch"
    return "proceed", "checks passed"


def _dose_str(d, val_key, unit_key):
    val = d.get(val_key)
    unit = d.get(unit_key)
    if val is None or (isinstance(val, float) and (val != val)):
        return None
    if unit:
        return f"{val}{unit}".replace(" ", "")
    return str(val).strip()


def _allergies_list(order):
    raw = order.get("allergies") or ""
    if not raw or (isinstance(raw, float) and raw != raw):
        return []
    return [a.strip().lower() for a in str(raw).split(",") if a.strip()]


def _drug_lower(drug):
    if drug is None or (isinstance(drug, float) and drug != drug):
        return ""
    return str(drug).strip().lower()


def evaluate_scenario(order, tray):
    """
    Run the full 8-step MedAssist check sequence. Returns a dict compatible with
    agent_runner and the frontend RunState: status, action, flag_code, tray_position,
    speak_message, check_results (step, name, status, flag?, message?), outcome.
    """
    tray_position = str(tray.get("tray_position", ""))
    ordered_drug = _drug_lower(tray.get("ordered_drug") or order.get("drug_name_generic"))
    ordered_dose = _dose_str(order, "dosage_value", "dosage_unit") or _dose_str(tray, "ordered_dose_value", "ordered_dose_unit")
    tray_drug = _drug_lower(tray.get("tray_drug"))
    tray_dose = _dose_str(tray, "tray_dose_value", "tray_dose_unit")
    dispensing_status = (order.get("dispensing_status") or "pending").strip().lower()
    high_alert = order.get("high_alert") in (True, "True", "true", "1")
    lasa_risk = order.get("lasa_risk") in (True, "True", "true", "1")
    lasa_pair = _drug_lower(order.get("lasa_pair") or "")
    allergies = _allergies_list(order)

    check_names = [
        "Allergy", "Already Dispensed", "LASA Confusion", "Drug Match",
        "Out of Range", "Dose Match", "High Alert", "All Clear",
    ]
    check_results = []
    outcome = "running"
    flag_code = "NONE"
    speak_message = ""

    # 1. Allergy
    tray_drug_in_allergy = any(a in (tray_drug or "") or (tray_drug or "") in a for a in allergies)
    if allergies and tray_drug_in_allergy:
        check_results.append({"step": 1, "name": "Allergy", "status": "failed", "flag": "FLAG_ALLERGY", "message": f"Tray drug matches patient allergen"})
        for i in range(2, 9):
            check_results.append({"step": i, "name": check_names[i - 1], "status": "pending"})
        return _rule_result("hold", "alert_human_staff", "ALLERGY", tray_position, check_results, "FLAG_ALLERGY",
                            "Patient allergy match. Halt.", check_results[0]["message"])
    check_results.append({"step": 1, "name": "Allergy", "status": "passed"})

    # 2. Already Dispensed
    if dispensing_status == "dispensed":
        check_results.append({"step": 2, "name": "Already Dispensed", "status": "failed", "flag": "FLAG_ALREADY_DISPENSED", "message": "Order already dispensed."})
        for i in range(3, 9):
            check_results.append({"step": i, "name": check_names[i - 1], "status": "pending"})
        return _rule_result("hold", "stop_and_wait", "ALREADY_DISPENSED", tray_position, check_results, "FLAG_ALREADY_DISPENSED",
                            "Order already dispensed. Prevents double-dosing.", check_results[1]["message"])
    check_results.append({"step": 2, "name": "Already Dispensed", "status": "passed"})

    # 3. LASA
    if lasa_risk and lasa_pair and _drug_lower(tray_drug) == lasa_pair:
        check_results.append({"step": 3, "name": "LASA Confusion", "status": "failed", "flag": "FLAG_LASA", "message": "Tray drug is LASA pair of ordered drug."})
        for i in range(4, 9):
            check_results.append({"step": i, "name": check_names[i - 1], "status": "pending"})
        return _rule_result("hold", "alert_human_staff", "LASA", tray_position, check_results, "FLAG_LASA",
                            "LASA confusion. Halt.", check_results[2]["message"])
    check_results.append({"step": 3, "name": "LASA Confusion", "status": "passed"})

    # 4. Drug Match
    if (ordered_drug or tray_drug) and ordered_drug != tray_drug:
        check_results.append({"step": 4, "name": "Drug Match", "status": "failed", "flag": "FLAG_WRONG_DRUG", "message": f"Ordered {ordered_drug}; tray has {tray_drug}."})
        for i in range(5, 9):
            check_results.append({"step": i, "name": check_names[i - 1], "status": "pending"})
        return _rule_result("hold", "alert_human_staff", "WRONG_DRUG", tray_position, check_results, "FLAG_WRONG_DRUG",
                            "Wrong drug. Halt.", check_results[3]["message"])
    check_results.append({"step": 4, "name": "Drug Match", "status": "passed"})

    # 5. Out of Range (simplified: e.g. digoxin > 0.25 mg)
    try:
        dose_val = float(tray.get("tray_dose_value") or tray.get("ordered_dose_value") or "0")
        dose_unit = (tray.get("tray_dose_unit") or tray.get("ordered_dose_unit") or "").strip().lower()
        if "digoxin" in (ordered_drug or "") and dose_unit == "mg" and dose_val > 0.25:
            check_results.append({"step": 5, "name": "Out of Range", "status": "failed", "flag": "FLAG_OUT_OF_RANGE", "message": "Digoxin dose exceeds therapeutic range."})
            for i in range(6, 9):
                check_results.append({"step": i, "name": check_names[i - 1], "status": "pending"})
            return _rule_result("hold", "alert_human_staff", "OUT_OF_RANGE", tray_position, check_results, "FLAG_OUT_OF_RANGE",
                                "Dose out of range.", check_results[4]["message"])
    except (TypeError, ValueError):
        pass
    check_results.append({"step": 5, "name": "Out of Range", "status": "passed"})

    # 6. Dose Match
    if ordered_dose != tray_dose:
        check_results.append({"step": 6, "name": "Dose Match", "status": "failed", "flag": "FLAG_WRONG_DOSE", "message": f"Ordered {ordered_dose}; tray has {tray_dose}."})
        for i in range(7, 9):
            check_results.append({"step": i, "name": check_names[i - 1], "status": "pending"})
        return _rule_result("hold", "alert_human_staff", "DOSE_HIGH" if (tray_dose or "") > (ordered_dose or "") else "DOSE_LOW", tray_position, check_results, "FLAG_WRONG_DOSE",
                            "Dose mismatch. Halt.", check_results[5]["message"])
    check_results.append({"step": 6, "name": "Dose Match", "status": "passed"})

    # 7. High Alert -> require verify (hold until human confirms)
    if high_alert:
        check_results.append({"step": 7, "name": "High Alert", "status": "passed"})  # passed check but outcome is verify pending
        check_results.append({"step": 8, "name": "All Clear", "status": "pending"})
        return _rule_result("hold", "stop_and_wait", "HIGH_ALERT", tray_position, check_results, "FLAG_HIGH_ALERT_VERIFY",
                            "High-alert medication. Secondary verification required.", "High-alert verification pending.")
    check_results.append({"step": 7, "name": "High Alert", "status": "passed"})

    # 8. All Clear
    check_results.append({"step": 8, "name": "All Clear", "status": "passed"})
    return _rule_result("proceed", "pick_vial", "NONE", tray_position, check_results, "dispense",
                        "Medication verified. Delivering now.", "All checks passed.")


def _rule_result(status, action, flag_code, tray_position, check_results, outcome, speak_message, _last_message):
    return {
        "status": status,
        "action": action,
        "flag_code": flag_code,
        "tray_position": tray_position,
        "speak_message": speak_message,
        "check_results": check_results,
        "outcome": outcome,
    }
