from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, abort

from .post_management import PostManager

from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.stroke_risk_score_v2.calc_risk_score import calculate_risk_score
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

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    syntrillo_internal_key_patient = post_manager.syntrillo_internal_key
    on_demand = (request.form.get('on_demand') == '1')

    try:

        risk_score, metrics, stroke_priority_score, independent_risk_variable_scores, dependent_risk_variable_contributions = calculate_risk_score(syntrillo_internal_key_patient, is_ondemand_srs=on_demand)
        if risk_score is None and stroke_priority_score is None:
            return jsonify({
                'success': True,
                'message': 'No data available',
                'data': {
                    'risk_score': risk_score,
                    'metrics': metrics,
                    'priority_score': stroke_priority_score,
                    'independent_risk_variable_scores': independent_risk_variable_scores,
                    'dependent_risk_variable_contributions': dependent_risk_variable_contributions
                }
            })

        if metrics['srs_response_data'] is not None:
            metrics['srs_response_data'] = metrics['srs_response_data'][0].model_dump()
        if metrics['lab_data'] is not None:
            metrics['lab_data'] = metrics['lab_data'].model_dump()

        # Return success response
        return jsonify({
            'success': True,
            'message': 'Charting note data received successfully',
            'data': {
                'risk_score': risk_score,
                'metrics': metrics,
                'priority_score': stroke_priority_score,
                'independent_risk_variable_scores': independent_risk_variable_scores,
                'dependent_risk_variable_contributions': dependent_risk_variable_contributions
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
    # iframe_validator = IframeValidator()
    # iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    # if not iframe_valid:
    #     abort(403, description="Access Denied")

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)
    syntrillo_internal_key_patient = post_manager.syntrillo_internal_key

    print(f"request.form: {request.form}")
    logger.info(f"request.form: {request.form}")

    try:
        # Get the form data from the request (FormData instead of JSON)
        form_data = {}

        # Only extract fields that are actually present in the form
        if request.form.get('Gender'):
            form_data['Gender'] = request.form.get('Gender')

        # if request.form.get('PhysicalInactivityHours'):
        form_data['PhysicalInactivityHours'] = float(request.form.get('PhysicalInactivityHours')) if (request.form.get('PhysicalInactivityHours') != 'NaN') else None
        form_data['PhysicalActivityMinutes'] = float(request.form.get('PhysicalActivityMinutes')) if (request.form.get('PhysicalActivityMinutes') != 'NaN') else None

        if request.form.get('HasPreviousStroke'):
            form_data['HasPreviousStroke'] = request.form.get('HasPreviousStroke') == 'yes'

        if request.form.get('NumberOfStrokes'):
            form_data['NumberOfStrokes'] = request.form.get('NumberOfStrokes')

        if request.form.get('LatestStrokeMechanism'):
            form_data['LatestStrokeMechanism'] = request.form.get('LatestStrokeMechanism')

        if request.form.get('ScreenedForTIA'):
            form_data['ScreenedForTIA'] = request.form.get('ScreenedForTIA') == 'yes'

        if request.form.get('LikelihoodOfTIA'):
            form_data['LikelihoodOfTIA'] = request.form.get('LikelihoodOfTIA')

        if request.form.get('TIAMechanism'):
            form_data['TIAMechanism'] = request.form.get('TIAMechanism')

        if request.form.get('HasPriorHeadCT'):
            form_data['HasPriorHeadCT'] = request.form.get('HasPriorHeadCT') == 'yes'

        if request.form.get('PriorCTDate'):
            try:
                form_data['PriorCTDate'] = datetime.strptime(request.form.get('PriorCTDate'), '%Y-%m-%d')
            except ValueError:
                form_data['PriorCTDate'] = None

        if request.form.get('ChronicInfarctPresent'):
            form_data['ChronicInfarctPresent'] = request.form.get('ChronicInfarctPresent') == 'yes'

        if request.form.get('ChronicInfarctMechanism'):
            form_data['ChronicInfarctMechanism'] = request.form.get('ChronicInfarctMechanism')

        if request.form.get('HistoryOfAtrialFibrillation'):
            form_data['HistoryOfAtrialFibrillation'] = request.form.get('HistoryOfAtrialFibrillation') == 'true'

        if request.form.get('HistoryOfIronDeficiencyAnemia'):
            form_data['HistoryOfIronDeficiencyAnemia'] = request.form.get('HistoryOfIronDeficiencyAnemia') == 'true'

        if request.form.get('AnemiaSeverity'):
            form_data['AnemiaSeverity'] = request.form.get('AnemiaSeverity')

        if request.form.get('HistoryOfArterialClots'):
            form_data['HistoryOfArterialClots'] = request.form.get('HistoryOfArterialClots') == 'true'

        if request.form.get('ArterialClotOccurrences'):
            form_data['ArterialClotOccurrences'] = request.form.get('ArterialClotOccurrences')

        if request.form.get('HistoryOfVenousClots'):
            form_data['HistoryOfVenousClots'] = request.form.get('HistoryOfVenousClots') == 'true'

        if request.form.get('VenousClotOccurrences'):
            form_data['VenousClotOccurrences'] = request.form.get('VenousClotOccurrences')

        if request.form.get('PFOPresence'):
            form_data['PFOPresence'] = request.form.get('PFOPresence')

        if request.form.get('HistoryOfCHF'):
            form_data['HistoryOfCHF'] = request.form.get('HistoryOfCHF') == 'true'

        if request.form.get('EjectionFraction'):
            form_data['EjectionFraction'] = request.form.get('EjectionFraction')

        if request.form.get('HistoryOfCarotidStenosis'):
            form_data['HistoryOfCarotidStenosis'] = request.form.get('HistoryOfCarotidStenosis') == 'true'

        if request.form.get('StenosisPercentage'):
            form_data['StenosisPercentage'] = request.form.get('StenosisPercentage')

        if request.form.get('HistoryOfOSA'):
            form_data['HistoryOfOSA'] = request.form.get('HistoryOfOSA') == 'true'

        if request.form.get('OSASeverity'):
            form_data['OSASeverity'] = request.form.get('OSASeverity')

        if request.form.get('HistoryOfCAD'):
            form_data['HistoryOfCAD'] = request.form.get('HistoryOfCAD') == 'true'

        if request.form.get('CADType'):
            form_data['CADType'] = request.form.get('CADType')

        if request.form.get('HistoryOfValvularHeartDisease'):
            form_data['HistoryOfValvularHeartDisease'] = request.form.get('HistoryOfValvularHeartDisease') == 'true'

        if request.form.get('HistoryOfCKD'):
            form_data['HistoryOfCKD'] = request.form.get('HistoryOfCKD') == 'true'

        if request.form.get('HistoryOfDiabetes'):
            form_data['HistoryOfDiabetes'] = request.form.get('HistoryOfDiabetes') == 'true'

        if request.form.get('HistoryOfObesity'):
            form_data['HistoryOfObesity'] = request.form.get('HistoryOfObesity') == 'true'

        if request.form.get('HemoglobinA1c'):
            try:
                form_data['HemoglobinA1c'] = float(request.form.get('HemoglobinA1c'))
            except (ValueError, TypeError):
                form_data['HemoglobinA1c'] = None

        if request.form.get('LDL'):
            try:
                form_data['LDL'] = float(request.form.get('LDL'))
            except (ValueError, TypeError):
                form_data['LDL'] = None

        if request.form.get('HDL'):
            try:
                form_data['HDL'] = float(request.form.get('HDL'))
            except (ValueError, TypeError):
                form_data['HDL'] = None

        if request.form.get('Triglycerides'):
            try:
                form_data['Triglycerides'] = float(request.form.get('Triglycerides'))
            except (ValueError, TypeError):
                form_data['Triglycerides'] = None

        if request.form.get('Creatinine'):
            try:
                form_data['Creatinine'] = float(request.form.get('Creatinine'))
            except (ValueError, TypeError):
                form_data['Creatinine'] = None

        # Handle compliance fields - only include if they exist
        compliance_data = {}
        compliance_fields = [
            'strokeCompliance',
            'tiaCompliance',
            'chronicInfarctCompliance',
            'atrialFibrillationCompliance',
            'ironDeficiencyAnemiaCompliance',
            'arterialClotsCompliance',
            'venousClotsCompliance',
            'chfCompliance',
            'carotidStenosisCompliance',
            'osaCompliance',
            'cadCompliance',
            'valvularHeartDiseaseCompliance',
            # 'ckdCompliance',
            # 'diabetesCompliance',
            # 'obesityCompliance',
            'hemoglobinA1cCompliance',
            'ldlCompliance',
            'hdlCompliance',
            'triglyceridesCompliance',
            'creatinineCompliance'
        ]

        for field in compliance_fields:
            if request.form.get(field):
                compliance_data[field] = request.form.get(field)

        if compliance_data:
            form_data['compliance'] = compliance_data
        else:
            form_data['compliance'] = {}

        print(f"form_data: {form_data}")
        logger.info(f"form_data: {form_data}")

        if not form_data:
            return jsonify({
                'success': False,
                'error': 'No form data received'
            }), 400

        # Log the received data for debugging
        current_app.logger.info(f"Received charting note data: {form_data}")

        # Remove internal fields before processing
        # omit_fields = ['healthie_user_id', 'healthie_provider_id', 'temporary_lookup_code', 'patient_not_registered_at_syntrillo']
        # processed_data = {k: v for k, v in form_data.items() if k not in omit_fields}

        # Log the processed data for debugging
        # current_app.logger.info(f"Processed charting note data: {processed_data}")

        # Insert the SRS form response into the database
        response_id, log = insert_srs_iframe_data(syntrillo_internal_key_patient, syntrillo_internal_key_clinician="", data=form_data)

        if log['success']:
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
