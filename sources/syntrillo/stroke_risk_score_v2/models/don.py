# Path: sources/syntrillo/stroke_risk_score_v2/models/don.py

DEFAULT_DATA_OBJECT_NOTATION = {
        "dependent_risk_variable_contributions": {
            "sps": {
                "afib": 0.041277302808999126,
                "chf": 0.045029784882544506,
                "hdl": 0.04240304743106274,
                "ldl": 0.045029784882544506,
                "recent_stroke": 0.041277302808999126,
                "triglycerides": 0.037524820735453754
            },
            "srs": {
                "afib": 0.14424257126947118,
                "chf": 0.15735553229396856,
                "hdl": 0.1481764595768204,
                "ldl": 0.15735553229396856,
                "recent_stroke": 0.14424257126947118,
                "triglycerides": 0.1311296102449738
            }
        },
        "independent_risk_variable_scores": {
            "sps": {
                "alcohol_use": 0.0883359403077741,
                "avg_dbp": 0.06795072331367238,
                "avg_peak_sbp": 0.06795072331367238,
                "avg_sbp": 0.06795072331367238,
                "cigarette_use": 0.13590144662734477,
                "creatinine": 0.12910637429597754,
                "hemoglobin_a1c": 0.16987680828418097,
                "marijuana_use": 0.08154086797640686,
                "physical_inactivity": 0.10192608497050858,
                "rhr": 0.06795072331367238,
                "sbp_std": 0.06795072331367238
            },
            "srs": {
                "alcohol_use": 0.010681611186484216,
                "avg_dbp": 0.010681611186484216,
                "avg_peak_sbp": 0.010681611186484216,
                "avg_sbp": 0.010681611186484216,
                "cigarette_use": 0.010681611186484216,
                "creatinine": 0.010681611186484216,
                "hemoglobin_a1c": 0.010681611186484216,
                "marijuana_use": 0.010681611186484216,
                "physical_inactivity": 0.010681611186484216,
                "rhr": 0.010681611186484216,
                "sbp_std": 0.010681611186484216
            }
        },
        "metrics": {
            "healthie_srs_data": {
                "activity_minutes_answer": None,
                "average_rhr_baseline": 57.56,
                "average_rhr_prior": None,
                "average_rhr_trailing": None,
                "inactivity_hours_answer": None,
                "ssq_score": None
            },
            "lab_data": {
                "creatintine_value": None,
                "hdl_value": None,
                "hemoglobin_value": None,
                "hgA1c_value": None,
                "hsCRP_value": None,
                "ldl_value": None
            },
            "srs_response_data": {
                "AnemiaSeverity": None,
                "ArterialClotOccurrences": None,
                "AvgSBP": None,
                "BMI": 34.58000183105469,
                "CADType": None,
                "ChronicInfarctMechanism": None,
                "ChronicInfarctPresent": None,
                "Creatinine": None,
                "EjectionFraction": "Unknown",
                "Gender": "man",
                "HDL": 29.0,
                "HDLLevel": "Low",
                "HasPreviousStroke": True,
                "HasPriorHeadCT": True,
                "Height": 72.0,
                "HemoglobinA1c": 5.5,
                "HistoryOfArterialClots": None,
                "HistoryOfAtrialFibrillation": True,
                "HistoryOfCAD": None,
                "HistoryOfCHF": True,
                "HistoryOfCKD": None,
                "HistoryOfCarotidStenosis": None,
                "HistoryOfHyperlipidemia": True,
                "HistoryOfIronDeficiencyAnemia": None,
                "HistoryOfOSA": None,
                "HistoryOfValvularHeartDisease": None,
                "HistoryOfVenousClots": None,
                "LDL": 150.0,
                "LDLLevel": "High",
                "LatestStrokeMechanism": "Cardioembolic",
                "LikelihoodOfTIA": None,
                "NumberOfStrokes": "One",
                "OSASeverity": None,
                "PFOPresence": None,
                "PhysicalActivityMinutes": None,
                "PhysicalInactivityHours": None,
                "PhysicalInactivityLevel": None,
                "PriorCTDate": "Fri, 02 May 2025 00:00:00 GMT",
                "RHR": None,
                "ScreenedForTIA": None,
                "StenosisPercentage": None,
                "TIAMechanism": None,
                "Triglycerides": None,
                "TriglyceridesLevel": "Unknown",
                "VenousClotOccurrences": None,
                "Weight": 255.0,
                "compliance": {
                    "arterialClotsCompliance": None,
                    "atrialFibrillationCompliance": "optimized",
                    "cadCompliance": None,
                    "carotidStenosisCompliance": None,
                    "chfCompliance": "not optimized",
                    "chronicInfarctCompliance": None,
                    "ckdCompliance": None,
                    "hdlCompliance": "partially optimized",
                    "ironDeficiencyAnemiaCompliance": None,
                    "ldlCompliance": "not optimized",
                    "osaCompliance": None,
                    "srs_form_response_id": 21,
                    "strokeCompliance": "optimized",
                    "tiaCompliance": None,
                    "triglyceridesCompliance": "not optimized",
                    "valvularHeartDiseaseCompliance": None,
                    "venousClotsCompliance": None
                },
                "created_at": "Sun, 07 Sep 2025 18:39:01 GMT",
                "srs_form_response_id": 21,
                "syntrillo_internal_key_clinician": "",
                "syntrillo_internal_key_patient": "5afb369d-376a-4750-bdcc-bb77287a0164"
            },
            "substance_use_data": {},
            "tenovi_bp_data": {
                "diastolic": {
                    "baseline": {
                        "average": 103.4
                    },
                    "trailing": {
                        "average": 69.5
                    }
                },
                "systolic": {
                    "baseline": {
                        "average": 161.0
                    },
                    "trailing": {
                        "Peak AVG SBP": 115.0,
                        "SBP Count (>= 175)": 0.0,
                        "average": 106.0,
                        "variability": 4.3
                    }
                }
            },
            "tenovi_hr_data": {
                "trailing_hr_average": None,
                "trailing_hr_variability": None
            }
        },
        "priority_score": 35.96,
        "risk_score": 4.1
    }
