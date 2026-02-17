{
    "metadata": {
        "patient_id": "90b0d9f0-9b21-4547-97c6-6e5de94b9722",
        "calculated_at": "2026-02-11T10:30:45Z",
        "calculation_duration_ms": 5234,
        "data_completeness": {
            "queries_attempted": 42,
            "queries_successful": 40,
            "missing_sources": ["substance_use"]
        }
    },
    "scores": {
        "srs": 2.35,
        "sps": 2.35
    },
    "risk_factors": [
        {
            "id": "avg_sbp_trailing",
            "display_name": "Average Systolic BP",
            "category": "independent",
            "tags": ["blood_pressure", "cardiovascular", "tenovi", "objective"],
            "source": "tenovi",
            "timeframe": {
                "type": "trailing",
                "duration_weeks": 4,
                "measurement_count": 45,
                "date_start": "2026-01-14",
                "date_end": "2026-02-11"
            },
            "value": {
                "raw": 124.21,
                "unit": "mmHg",
                "risk_level": "low_intermediate",  # LOW, LOW_INTERMEDIATE, etc.
                "threshold_info": {
                    "current_range": [120, 130],
                    "next_threshold": 130
                }
            },
            "contribution": {
                "srs_absolute": 0.245,
                "sps_absolute": 0.245,
                "srs_percentage": 12.3,  # % of total SRS
                "sps_percentage": 12.3,
                "weight_applied": 1.5
            },
            "related_metrics": ["sbp_std_trailing", "avg_peak_sbp_trailing"]
        },
        {
            "id": "sbp_std_trailing",
            "display_name": "Systolic BP Variability",
            "category": "independent",
            "tags": ["blood_pressure", "cardiovascular", "tenovi", "objective"],
            "source": "tenovi",
            "timeframe": {
                "type": "trailing",
                "duration_weeks": 4,
                "measurement_count": 45,
                "date_start": "2026-01-14",
                "date_end": "2026-02-11"
            },
            "value": {
                "raw": 9.30,
                "unit": "mmHg (std dev)",
                "risk_level": "low",
                "threshold_info": null
            },
            "contribution": {
                "srs_absolute": 0.149,
                "sps_absolute": 0.149,
                "srs_percentage": 7.5,
                "sps_percentage": 7.5,
                "weight_applied": 1.25
            },
            "related_metrics": ["avg_sbp_trailing"]
        },
        {
            "id": "cad",
            "display_name": "Coronary Artery Disease",
            "category": "dependent",
            "tags": ["medical_history", "cardiovascular", "subjective"],
            "source": "srs_form",
            "timeframe": null,
            "value": {
                "raw": "Asymptomatic single vessel",
                "unit": null,
                "risk_level": "intermediate_high",
                "has_condition": true
            },
            "contribution": {
                "srs_absolute": 0.123,
                "sps_absolute": 0.123,
                "srs_percentage": 6.2,
                "sps_percentage": 6.2,
                "base_risk_factor": 1.75,
                "treatment_efficacy": 0.7,
                "treatment_optimization": 1.0
            },
            "compliance": {
                "status": "optimized",
                "compliance_value": 1.0
            },
            "related_metrics": null
        },
        {
            "id": "physical_inactivity",
            "display_name": "Physical Inactivity",
            "category": "independent",
            "tags": ["lifestyle", "activity", "healthie", "subjective"],
            "source": "healthie",
            "timeframe": {
                "type": "latest_response",
                "response_date": "2026-02-05"
            },
            "value": {
                "raw": 5.0,
                "unit": "hours/day",
                "risk_level": "intermediate_high"
            },
            "contribution": {
                "srs_absolute": 0.078,
                "sps_absolute": 0.078,
                "srs_percentage": 3.9,
                "sps_percentage": 3.9,
                "weight_applied": 1.75
            },
            "related_metrics": ["activity_minutes"]
        }
    ],
    "summary": {
        "by_category": {
            "independent": {
                "srs_contribution": 0.512,
                "sps_contribution": 0.512,
                "metric_count": 6
            },
            "dependent": {
                "srs_contribution": 0.487,
                "sps_contribution": 0.487,
                "metric_count": 3
            }
        },
        "by_tag": {
            "blood_pressure": { "srs_contribution": 0.394, "metric_count": 3 },
            "lifestyle": { "srs_contribution": 0.078, "metric_count": 2 },
            "lab_values": { "srs_contribution": 0.222, "metric_count": 3 }
        },
        "top_contributors": [
            { "id": "avg_sbp_trailing", "srs_contribution": 0.245 },
            { "id": "ldl", "srs_contribution": 0.182 },
            { "id": "sbp_std_trailing", "srs_contribution": 0.149 }
        ]
    }
}
