from flask import Blueprint, render_template, request, jsonify, current_app, abort, Response, send_file
import pandas as pd
import json
import base64
import io
from datetime import datetime
import uuid


from .post_management import PostManager
from syntrillo.remote_monitoring.data_reporting_combined import DataReportingCombination
from syntrillo.remote_monitoring.data_reporting_medication_adherence import DataReportingMedicationAdherence
from syntrillo.remote_monitoring.data_reporting_blood_pressure import DataReportingBloodPressure
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.remote_monitoring.data_reporting_heart_rate import DataReportingHeartRate
from syntrillo.remote_monitoring.data_reporting_steps import DataReportingSteps
from syntrillo.data_structures.healthie_dataset_handler import DataStructureHealthieDatasetHandler
from syntrillo.stroke_risk_score.risk_score import StrokeRiskScore
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement

from syntrillo.api_healthie.medications import HealthieMedications

from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.stroke_risk_score_v2.calc_risk_score import calculate_risk_score
from syntrillo.stroke_risk_score_v2.models.srs_form import SRSFormResponse
from syntrillo.stroke_risk_score_v2.agg_data import aggregate_data
from syntrillo.stroke_risk_score_v2.srs_iframe_db import insert_srs_iframe_data

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

    """

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # Deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    healthie_provider_id = request.form.get('healthie_provider_id')
    healthie_user_id = request.form.get('healthie_user_id')
    temporary_lookup_code = request.form.get('temporary_lookup_code')
    patient_not_registered_at_syntrillo_str = request.form.get('patient_not_registered_at_syntrillo')

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    syntrillo_internal_key_patient = post_manager.syntrillo_internal_key

    try:

        risk_score, metrics, stroke_priority_score = calculate_risk_score(syntrillo_internal_key_patient)

        metrics['srs_response_data'] = metrics['srs_response_data'][0].model_dump()

        # Return success response
        return jsonify({
            'success': True,
            'message': 'Charting note data received successfully',
            'data': {
                'risk_score': risk_score,
                'metrics': metrics,
                'priority_score': stroke_priority_score
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error retrieving risk score data: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500



@iframe_healthie_provider_tab_risk_score_bp.route('/healthie/iframe_provider_tab/risk_score/charting_note', methods=['POST'])
def iframe_healthie_provider_tab_risk_score_charting_note():
    """

    This endpoint is used to save the charting note form data.

    """
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        abort(403, description="Access Denied")

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)
    syntrillo_internal_key_patient = post_manager.syntrillo_internal_key

    print(f"request.form: {request.form}")

    try:
        # Get the form data from the request (FormData instead of JSON)
        form_data = {}
        # Extract form fields manually from request.form
        form_data['Gender'] = request.form.get('Gender') or None
        form_data['HasPreviousStroke'] = request.form.get('HasPreviousStroke') == 'yes'
        form_data['NumberOfStrokes'] = request.form.get('NumberOfStrokes') or None
        form_data['LatestStrokeMechanism'] = request.form.get('LatestStrokeMechanism') or None
        form_data['ScreenedForTIA'] = request.form.get('ScreenedForTIA') == 'yes'
        form_data['LikelihoodOfTIA'] = request.form.get('LikelihoodOfTIA') or None
        form_data['TIAMechanism'] = request.form.get('TIAMechanism') or None
        form_data['HasPriorHeadCT'] = request.form.get('HasPriorHeadCT') == 'yes'
        form_data['PriorCTDate'] = request.form.get('PriorCTDate') or None
        form_data['ChronicInfarctPresent'] = request.form.get('ChronicInfarctPresent') == 'yes'
        form_data['HistoryOfAtrialFibrillation'] = request.form.get('HistoryOfAtrialFibrillation') == 'true'
        form_data['HistoryOfIronDeficiencyAnemia'] = request.form.get('HistoryOfIronDeficiencyAnemia') == 'true'
        form_data['HistoryOfArterialClots'] = request.form.get('HistoryOfArterialClots') == 'true'
        form_data['HistoryOfVenousClots'] = request.form.get('HistoryOfVenousClots') == 'true'
        form_data['HistoryOfCHF'] = request.form.get('HistoryOfCHF') == 'true'
        form_data['HistoryOfCarotidStenosis'] = request.form.get('HistoryOfCarotidStenosis') == 'true'
        form_data['HistoryOfOSA'] = request.form.get('HistoryOfOSA') == 'true'
        form_data['HistoryOfCAD'] = request.form.get('HistoryOfCAD') == 'true'
        form_data['HistoryOfValvularHeartDisease'] = request.form.get('HistoryOfValvularHeartDisease') == 'true'
        form_data['HistoryOfCKD'] = request.form.get('HistoryOfCKD') == 'true'
        # form_data['HistoryOfHyperlipidemia'] = request.form.get('HistoryOfHyperlipidemia') == 'true'
        form_data['HistoryOfDiabetes'] = request.form.get('HistoryOfDiabetes') == 'true'
        form_data['HistoryOfObesity'] = request.form.get('HistoryOfObesity') == 'true'
        form_data['AnemiaSeverity'] = request.form.get('AnemiaSeverity') or None
        form_data['ArterialClotOccurrences'] = request.form.get('ArterialClotOccurrences') or None
        form_data['VenousClotOccurrences'] = request.form.get('VenousClotOccurrences') or None
        form_data['PFOPresence'] = request.form.get('PFOPresence') or None
        form_data['EjectionFraction'] = request.form.get('EjectionFraction') or None
        form_data['StenosisPercentage'] = request.form.get('StenosisPercentage') or None
        form_data['OSASeverity'] = request.form.get('OSASeverity') or None
        form_data['CADType'] = request.form.get('CADType') or None
        form_data['PhysicalInactivityHours'] = request.form.get('PhysicalInactivityHours') or None
        form_data['HemoglobinA1c'] = request.form.get('HemoglobinA1c') or None
        # form_data['LDLLevel'] = request.form.get('LDLLevel') or None
        # form_data['HDLLevel'] = request.form.get('HDLLevel') or None
        form_data['LDL'] = request.form.get('LDL') or None
        form_data['LDLCompliance'] = request.form.get('LDLCompliance') or None
        form_data['HDL'] = request.form.get('HDL') or None
        form_data['Triglycerides'] = request.form.get('Triglycerides') or None
        # form_data['TriglyceridesCompliance'] = request.form.get('TriglyceridesCompliance') or None
        form_data['Creatinine'] = request.form.get('Creatinine') or None
        form_data['ChronicInfarctMechanism'] = request.form.get('ChronicInfarctMechanism') or None
        # form_data['Height'] = request.form.get('Height') or None
        # form_data['Weight'] = request.form.get('Weight') or None
        # form_data['AvgSBP'] = request.form.get('AvgSBP') or None
        # form_data['RHR'] = request.form.get('RHR') or None
        # form_data['BMI'] = request.form.get('BMI') or None

        # Parse compliance data from JSON string
        compliance_json = request.form.get('compliance')
        if compliance_json:
            try:
                form_data['compliance'] = json.loads(compliance_json)
            except json.JSONDecodeError:
                form_data['compliance'] = {}
        else:
            form_data['compliance'] = {}

        print(f"form_data: {form_data}")

        if not form_data:
            return jsonify({
                'success': False,
                'error': 'No form data received'
            }), 400

        # Log the received data for debugging
        current_app.logger.info(f"Received charting note data: {form_data}")

        # Convert form data to proper types before passing to insert_srs_iframe_data
        processed_data = {}

        omit_fields = ['healthie_user_id', 'healthie_provider_id', 'temporary_lookup_code', 'patient_not_registered_at_syntrillo']
        # Copy all fields from form_data (booleans are already handled in frontend)
        for key, value in form_data.items():
            if key not in omit_fields:
                processed_data[key] = value

        # Handle numeric fields (ensure they're floats)
        numeric_fields = ['Height', 'Weight', 'AvgSBP', 'RHR', 'HemoglobinA1c', 'CreatineLevel']
        for field in numeric_fields:
            if field in processed_data and processed_data[field] is not None:
                try:
                    processed_data[field] = float(processed_data[field]) if processed_data[field] != "" else None
                except (ValueError, TypeError):
                    processed_data[field] = None

        # Handle date field
        if 'PriorCTDate' in processed_data and processed_data['PriorCTDate']:
            try:
                processed_data['PriorCTDate'] = datetime.fromisoformat(processed_data['PriorCTDate'])
            except (ValueError, TypeError):
                processed_data['PriorCTDate'] = None

        # Log the processed data for debugging
        current_app.logger.info(f"Processed charting note data: {processed_data}")


        # Add breakpoint to debug the exact issue
        # breakpoint()

        # Insert the SRS form response into the database
        response_id, log = insert_srs_iframe_data(syntrillo_internal_key_patient, syntrillo_internal_key_clinician="", data=processed_data)

        if log['success'] == True:
            return jsonify({
                'success': True,
                'message': 'Charting note data received successfully',
                'data': {
                    'response_id': response_id,
                    'timestamp': datetime.now().isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to insert charting note data',
                'error': log['error']
            }), 500

    except Exception as e:
        current_app.logger.error(f"Error processing charting note: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500
