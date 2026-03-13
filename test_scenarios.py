"""
Medical scenarios for testing the MedAssist system
"""

MEDICAL_SCENARIOS = {
    "medication_mismatch": {
        "description": "A robot scanned acetaminophen 500mg, but the patient order says ibuprofen 200mg. What should it do?",
        "patient_data": {
            "patient_id": "104",
            "ordered_medication": "ibuprofen 200mg",
            "scanned_medication": "acetaminophen 500mg",
            "allergies": [],
            "medical_history": []
        },
        "expected_priority": "high",
        "safety_critical": True
    },

    "failed_patient_scan": {
        "description": "Robot needs to deliver medication but patient wristband scan failed. Medication scan successful.",
        "patient_data": {
            "patient_id": "unknown",
            "room_number": "237A",
            "medication": "lisinopril 10mg",
            "scan_status": "wristband_failed"
        },
        "expected_priority": "high",
        "safety_critical": True
    },

    "elevated_vitals": {
        "description": "Patient monitoring shows: Temperature 102.1°F, Heart Rate 125 bpm, Blood Pressure 160/95 mmHg, O2 Sat 94%",
        "patient_data": {
            "patient_id": "305",
            "vitals": {
                "temperature": 102.1,
                "heart_rate": 125,
                "blood_pressure": "160/95",
                "oxygen_saturation": 94
            },
            "baseline_vitals": {
                "temperature": 98.6,
                "heart_rate": 72,
                "blood_pressure": "120/80",
                "oxygen_saturation": 98
            }
        },
        "expected_priority": "high",
        "safety_critical": True
    },

    "medication_allergy_alert": {
        "description": "Robot is about to administer penicillin to a patient with documented penicillin allergy.",
        "patient_data": {
            "patient_id": "456",
            "medication": "penicillin 500mg",
            "allergies": ["penicillin", "sulfa"],
            "medical_history": ["pneumonia", "hypertension"]
        },
        "expected_priority": "critical",
        "safety_critical": True
    },

    "insulin_administration": {
        "description": "Patient requires insulin injection. Blood glucose is 245 mg/dL. Patient is conscious and alert.",
        "patient_data": {
            "patient_id": "789",
            "blood_glucose": 245,
            "insulin_type": "Humalog",
            "prescribed_dose": "8 units",
            "last_meal": "2 hours ago",
            "consciousness_level": "alert and oriented"
        },
        "expected_priority": "medium",
        "safety_critical": True
    },

    "emergency_call": {
        "description": "Patient pressed emergency call button. Robot responds and finds patient on floor, conscious but in pain.",
        "patient_data": {
            "patient_id": "234",
            "location": "room_floor",
            "consciousness": "conscious",
            "reported_pain": "severe_leg_pain",
            "vital_signs": "unknown"
        },
        "expected_priority": "critical",
        "safety_critical": True
    },

    "scheduled_medication": {
        "description": "Time for scheduled morning medications. Patient is awake and ready.",
        "patient_data": {
            "patient_id": "567",
            "medications": [
                {"name": "lisinopril", "dose": "10mg", "time": "08:00"},
                {"name": "metformin", "dose": "500mg", "time": "08:00"},
                {"name": "atorvastatin", "dose": "20mg", "time": "08:00"}
            ],
            "current_time": "08:05",
            "patient_status": "awake_and_alert"
        },
        "expected_priority": "medium",
        "safety_critical": False
    },

    "unusual_vital_pattern": {
        "description": "Patient's heart rate has been gradually increasing over 4 hours: 72→85→98→112 bpm. No other changes.",
        "patient_data": {
            "patient_id": "890",
            "heart_rate_trend": [72, 85, 98, 112],
            "time_intervals": ["00:00", "01:00", "02:00", "03:00"],
            "other_vitals": {
                "temperature": 98.8,
                "blood_pressure": "125/82",
                "oxygen_saturation": 97
            }
        },
        "expected_priority": "medium",
        "safety_critical": False
    },

    "conflicting_orders": {
        "description": "Two different doctors have entered conflicting medication orders for the same patient.",
        "patient_data": {
            "patient_id": "345",
            "order_1": {
                "doctor": "Dr. Smith",
                "medication": "ibuprofen 400mg",
                "frequency": "every 6 hours",
                "timestamp": "2024-01-15 08:00"
            },
            "order_2": {
                "doctor": "Dr. Johnson",
                "medication": "acetaminophen 650mg",
                "frequency": "every 4 hours",
                "timestamp": "2024-01-15 10:30"
            }
        },
        "expected_priority": "high",
        "safety_critical": True
    },

    "medication_refusal": {
        "description": "Patient refuses to take prescribed antibiotic, claiming it makes them feel worse.",
        "patient_data": {
            "patient_id": "678",
            "medication": "amoxicillin 875mg",
            "reason_for_refusal": "makes me feel worse",
            "treatment_importance": "high",
            "infection_type": "pneumonia"
        },
        "expected_priority": "medium",
        "safety_critical": False
    }
}

# Vital signs reference ranges for assessment
VITAL_SIGNS_NORMAL_RANGES = {
    "temperature": {
        "normal_min": 97.0,
        "normal_max": 99.5,
        "unit": "°F"
    },
    "heart_rate": {
        "normal_min": 60,
        "normal_max": 100,
        "unit": "bpm"
    },
    "systolic_bp": {
        "normal_min": 90,
        "normal_max": 140,
        "unit": "mmHg"
    },
    "diastolic_bp": {
        "normal_min": 60,
        "normal_max": 90,
        "unit": "mmHg"
    },
    "oxygen_saturation": {
        "normal_min": 95,
        "normal_max": 100,
        "unit": "%"
    }
}

# Common medication categories and their safety considerations
MEDICATION_SAFETY_INFO = {
    "pain_relievers": {
        "medications": ["ibuprofen", "acetaminophen", "aspirin"],
        "contraindications": ["liver_disease", "kidney_disease", "bleeding_disorders"],
        "max_daily_doses": {
            "ibuprofen": "3200mg",
            "acetaminophen": "4000mg",
            "aspirin": "4000mg"
        }
    },
    "antibiotics": {
        "medications": ["amoxicillin", "penicillin", "cephalexin"],
        "contraindications": ["known_allergies"],
        "common_allergies": ["penicillin", "sulfa"]
    },
    "cardiac_medications": {
        "medications": ["lisinopril", "atorvastatin", "metoprolol"],
        "contraindications": ["hypotension", "bradycardia"],
        "monitoring_required": ["blood_pressure", "heart_rate"]
    },
    "diabetes_medications": {
        "medications": ["insulin", "metformin", "glipizide"],
        "contraindications": ["severe_kidney_disease"],
        "monitoring_required": ["blood_glucose", "kidney_function"]
    }
}

# Emergency protocols
EMERGENCY_PROTOCOLS = {
    "medication_error": {
        "immediate_actions": [
            "Stop medication administration",
            "Alert healthcare provider immediately",
            "Monitor patient for adverse reactions",
            "Document the incident"
        ],
        "priority": "critical"
    },
    "allergic_reaction": {
        "immediate_actions": [
            "Stop allergen exposure",
            "Call for medical assistance",
            "Prepare epinephrine if available",
            "Monitor vital signs continuously"
        ],
        "priority": "critical"
    },
    "vital_signs_critical": {
        "immediate_actions": [
            "Alert medical team immediately",
            "Increase monitoring frequency",
            "Prepare for potential interventions",
            "Document all readings"
        ],
        "priority": "critical"
    },
    "patient_fall": {
        "immediate_actions": [
            "Do not move patient",
            "Call for medical assistance",
            "Check for consciousness and vital signs",
            "Keep patient calm and still"
        ],
        "priority": "critical"
    }
}