from flask import Blueprint, render_template, request, jsonify, current_app, abort, Response, send_file
import pandas as pd
import json
import base64
import io
from datetime import datetime

from .post_management import PostManager
from syntrillo.remote_monitoring.data_reporting_combined import DataReportingCombination
from syntrillo.remote_monitoring.data_reporting_medication_adherence import DataReportingMedicationAdherence
from syntrillo.remote_monitoring.data_reporting_blood_pressure import DataReportingBloodPressure
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.remote_monitoring.data_reporting_heart_rate import DataReportingHeartRate
from syntrillo.remote_monitoring.data_reporting_steps import DataReportingSteps
from syntrillo.data_structures.healthie_dataset_handler import DataStructureHealthieDatasetHandler
from syntrillo.stroke_risk_score.risk_score import StrokeRiskScore

from syntrillo.api_healthie.medications import HealthieMedications

from syntrillo.system.iframe_validator import IframeValidator

iframe_healthie_provider_tab_risk_score_bp = Blueprint('iframe_healthie_provider_tab_risk_score_bp', __name__)

from syntrillo.system.logger import logger


@iframe_healthie_provider_tab_risk_score_bp.route('/healthie/iframe_provider_tab/risk_score', methods=['GET','POST'])
def iframe_healthie_provider_tab_risk_score():
    """

    This endpoint is used to display risk score tab, which is called by the healthie_iframe_provider_tab index.html.

    Visualizes risk score section breakdown and all metrics attributed, retrieved by route below.

    To do:
        - Add form to html to allow provider options to:
            a. show/hide patient name
            b. custom name report

    """
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        abort(403, description="Access Denied")


    healthie_provider_id = request.form.get('healthie_provider_id')
    healthie_user_id = request.form.get('healthie_user_id')
    temporary_lookup_code = request.form.get('temporary_lookup_code')
    patient_not_registered_at_syntrillo_str = request.form.get('patient_not_registered_at_syntrillo')

    return render_template(
        'healthie/iframe_provider_tab/risk_score.html',
        healthie_provider_id=healthie_provider_id,
        healthie_user_id=healthie_user_id,
        temporary_lookup_code=temporary_lookup_code,
        patient_not_registered_at_syntrillo=(patient_not_registered_at_syntrillo_str == 'True')
    )


@iframe_healthie_provider_tab_risk_score_bp.route('/healthie/iframe_provider_tab/risk_score/data', methods=['POST'])
def iframe_healthie_provider_tab_risk_score_data():
    """

    This endpoint is used to retrieve risk score data.

    Returns:
        {
            'total_score': 11.6,
            'data': {
                'i': (
                    6.3,
                    {
                        'etiology': 'Cardioembolic',
                        'medications': {
                            'statins support oral miscellaneous': {
                                'classification': 'statin',
                                'instructions': '|1117e253-936b-4040-814c-0ac3837674bc',
                                'compliance': None
                            },
                            'plavix oral tablet': {
                                'classification': 'antiplatelet',
                                'instructions': '|8a608885-f70a-4785-aeb7-3fe5ef8a1352',
                                'compliance': None
                            }
                        },
                        'lab_values': {
                            'ldl': (True, 77),
                            'ha1c': (False, 8)
                        },
                        'history': {
                            'carotid_stenosis': True,
                            'afib': True,
                            'diabetes': True,
                            'sleep_apnea': True,
                            'smoker': False,
                            'smoking_frequency': 15,
                            'cpap_prescription': True,
                            'cpap_use': False,
                            'cpap_usage': True
                        }
                    }
                ),
                'ii': (
                    0,
                    {
                        'cta_performed': True,
                        'cardiac_monitoring_30day': True,
                        'ha1c_6mo': True
                    }
                ),
                'iii': (
                    3,
                    {
                        'sbp': 140,
                        'dbp': 95
                    }
                ),
                'iv': (
                    1.7,
                    {
                        'mod_exercise': '140',
                        'vig_exercise': '30'
                    }
                ),
                'v': (
                    0.0,
                    {
                        'bmi': 25.4
                    }
                ),
                'vii': (
                    0.3,
                    {
                        'resting_hr': '72'
                    }
                ),
                'viii': (
                    0,
                    {
                        'packs_per_day': 'Between half a pack and a pack (10-20 cigarettes)'
                    }
                )
            }
        }

    """

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # Deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    data_reporting_risk_score = StrokeRiskScore(post_manager.syntrillo_internal_key)

    risk_score = data_reporting_risk_score.calculate_risk_score()

    return jsonify({
        "risk_score": risk_score
    })
