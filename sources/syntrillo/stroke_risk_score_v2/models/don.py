# Path: sources/syntrillo/stroke_risk_score_v2/models/don.py

DEFAULT_DATA_OBJECT_NOTATION = {
        "dependent_risk_variable_contributions": {
            "sps": {
                "cad": 0.123,
                # "hdl": 0.182,
                "ldl": 0.182,
                "triglycerides": 0.182,
            },
            "srs": {
                "cad": 0.123,
                # "hdl": 0.182,
                "ldl": 0.182,
                "triglycerides": 0.182,
            }
        },
        "independent_risk_variable_scores": {
            "sps": {
                "avg_sbp": 0.245,
                "creatinine": 0.04,
                "physical_inactivity": 0.078,
                "sbp_std": 0.149
            },
            "srs": {
                "avg_sbp": 0.245,
                "creatinine": 0.04,
                "physical_inactivity": 0.078,
                "sbp_std": 0.149
            }
        },
        "metrics": {
            "healthie_srs_data": {
                "activity_minutes_answer": None,
                "average_rhr_baseline": None,
                "average_rhr_prior": None,
                "average_rhr_trailing": None,
                "inactivity_hours_answer": 5.0,
                "ssq_score": None
            },
            "lab_data": {
                "creatintine_value": 1.2,
                "hdl_value": 51.0,
                "hemoglobin_value": 5.4,
                "hgA1c_value": 5.4,
                "hsCRP_value": None,
                "ldl_value": 100.0
            },
            "srs_response_data": {
                "AnemiaSeverity": None,
                "ArterialClotOccurrences": None,
                "AvgSBP": None,
                "BMI": 25.84000015258789,
                "CADType": "Asymptomatic single vessel",
                "ChronicInfarctMechanism": None,
                "ChronicInfarctPresent": None,
                "Creatinine": 1.2000000476837158,
                "EjectionFraction": None,
                "Gender": "man",
                "HDL": 51.0,
                "HDLLevel": None,
                "HasPreviousStroke": False,
                "HasPriorHeadCT": False,
                "Height": 69.0,
                "HemoglobinA1c": 5.400000095367432,
                "HistoryOfArterialClots": None,
                "HistoryOfAtrialFibrillation": None,
                "HistoryOfCAD": True,
                "HistoryOfCHF": None,
                "HistoryOfCKD": None,
                "HistoryOfCarotidStenosis": None,
                "HistoryOfHyperlipidemia": True,
                "HistoryOfIronDeficiencyAnemia": None,
                "HistoryOfOSA": None,
                "HistoryOfValvularHeartDisease": None,
                "HistoryOfVenousClots": None,
                "LDL": 100.0,
                "LDLLevel": "Borderline",
                "LatestStrokeMechanism": None,
                "LikelihoodOfTIA": None,
                "NumberOfStrokes": None,
                "OSASeverity": None,
                "PFOPresence": None,
                "PhysicalActivityMinutes": None,
                "PhysicalInactivityHours": None,
                "PhysicalInactivityLevel": None,
                "PriorCTDate": None,
                "RHR": None,
                "ScreenedForTIA": False,
                "StenosisPercentage": None,
                "TIAMechanism": None,
                "Triglycerides": 154.0,
                "TriglyceridesLevel": "Moderate",
                "VenousClotOccurrences": None,
                "Weight": 175.0,
                "compliance": {
                    "arterialClotsCompliance": None,
                    "atrialFibrillationCompliance": None,
                    "cadCompliance": "optimized",
                    "carotidStenosisCompliance": None,
                    "chfCompliance": None,
                    "chronicInfarctCompliance": None,
                    "ckdCompliance": None,
                    "hdlCompliance": None,
                    "ironDeficiencyAnemiaCompliance": None,
                    "ldlCompliance": "not optimized",
                    "osaCompliance": None,
                    "srs_form_response_id": 24,
                    "strokeCompliance": None,
                    "tiaCompliance": None,
                    "triglyceridesCompliance": "not optimized",
                    "valvularHeartDiseaseCompliance": None,
                    "venousClotsCompliance": None
                },
                "created_at": "Thu, 08 Jan 2026 19:29:30 GMT",
                "srs_form_response_id": 24,
                "syntrillo_internal_key_clinician": "Unknown",
                "syntrillo_internal_key_patient": "90b0d9f0-9b21-4547-97c6-6e5de94b9722"
            },
            "substance_use_data": {},
            "tenovi_bp_data": {
                "diastolic": {
                    "baseline": {
                        "average": 83.0
                    },
                    "trailing": {
                        "average": None,
                    }
                },
                "systolic": {
                    "baseline": {
                        "average": 130.2,
                        "variability": 13.1,
                        "Peak AVG SBP": 152.0,
                    },
                    "trailing": {
                        "Peak AVG SBP": None,
                        "SBP Count (>= 175)": None,
                        "average": None,
                        "variability": None
                    }
                }
            },
            "tenovi_hr_data": {
                "trailing_hr_average": 55.41,
                "trailing_hr_variability": 6.87
            }
        },
        "priority_score": 2.35,
        "risk_score": 2.35
    }
