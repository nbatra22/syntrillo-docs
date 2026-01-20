from flask import Blueprint, render_template, request, jsonify, abort, send_file, current_app
import pandas as pd
import io
from io import BytesIO
import os
from datetime import datetime
import secrets
import string

from .post_management import PostManager

from syntrillo.api_healthie.constants import RHR_CATEGORY, WEIGHT_CATEGORY
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.bp_analysis.bp_report import BloodPressureReport
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.api_healthie.user import HealthieUser
from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.stroke_risk_score_v2.utils import get_biometric_data, calculate_bmi, get_patient_info
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.system.logger import logger
from syntrillo.stroke_risk_score_v2.agg_data import (
    get_srs_healthie_data,
    get_healthie_metric_data,
    calc_rhr_metadata,
    get_healthie_activity_and_inactivity_module_ids
)

iframe_healthie_provider_tab_bp_analysis_bp = Blueprint('iframe_healthie_provider_tab_bp_analysis_bp', __name__)


# @iframe_healthie_provider_tab_bp_analysis.route('/healthie/iframe_provider_tab/blood_pressure', methods=['POST'])
# def iframe_healthie_provider_tab_blood_pressure():
#     """
#     This endpoint is used to display blood pressure analysis table and a pdf download,
#     which is called by the healthie_iframe_provider_tab index.html.

#     The pdf can be viewed in sources/bp_analysis/reports.
#     """

#     return render_template(
#         'healthie/iframe_provider_tab/blood_pressure.html',
#     )

@iframe_healthie_provider_tab_bp_analysis_bp.route('/healthie/iframe_provider_tab/blood_pressure', methods=['GET','POST'])
def iframe_healthie_provider_tab_blood_pressure():
    """

    This endpoint is used to display blood pressure tab, which is called by the healthie_iframe_provider_tab index.html.

    Visualizes blood pressure analysis table and a pdf download button.

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
        'healthie/iframe_provider_tab/blood_pressure.html',
        healthie_provider_id=healthie_provider_id,
        healthie_user_id=healthie_user_id,
        temporary_lookup_code=temporary_lookup_code,
        patient_not_registered_at_syntrillo=(patient_not_registered_at_syntrillo_str == 'True')
    )

@iframe_healthie_provider_tab_bp_analysis_bp.route('/healthie/iframe_provider_tab/blood_pressure/analysis', methods=['POST'])
def iframe_healthie_provider_tab_blood_pressure_analysis():

    start_date_str = request.form.get("start_date", "").strip() or None
    end_date_str = request.form.get("end_date", "").strip() or None

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # Deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # Establish connection to BloodPressureAnalysis class
    data_reporting_blood_pressure = BloodPressureAnalysis(post_manager.syntrillo_internal_key)

    # Get all available blood pressure data
    _, log = data_reporting_blood_pressure.get_blood_pressure_dataframe(
        start_date,
        end_date,
    )

    # Confirm blood pressure data is pulled
    if log['success'] == False:
        return jsonify({'error': f"{log['error']}" })

    # Handle patients with no blood pressure measurements
    if _.empty:
        return jsonify({
            'error': 'Insufficient data. Patient has recorded zero measurements.',
        })

    # Generate analysis + extremes table using BloodPressureAnalysis class methods
    timeframes = data_reporting_blood_pressure.calculate_timeframes() # Sorts and separates data by Baseline, Prior, & Current, in two week increments
    summary_stats = data_reporting_blood_pressure.calculate_summary_stats(hide_intervention=False) # Calculates summary stats for each timeframe
    analysis_table = data_reporting_blood_pressure.get_analysis_table() # Calculates row values for each timeframe
    # analysis_table_with_inception = data_reporting_blood_pressure.calculate_since_baseline(metadata, analysis_table) # Appends 3 additional columns for lifetime calculations

    # Remove specific rows from analysis_table
    rows_to_remove = [
        # 'SBP SD (mmHg)',
        # 'DBP SD (mmHg)',
        'SBP CV (%)',
        'DBP CV (%)',
        'SBP Count (>= 175)'
    ]
    analysis_table = analysis_table[~analysis_table.index.isin(rows_to_remove)]

    analysis_table.rename(index={
        'Hypotensive Count⁴': 'Near-Hypotensive Events⁴'
    }, inplace=True)

    extremes = data_reporting_blood_pressure.calculate_extremes().reset_index(drop=True) # Returns table for all rows (timestamp, sbp, dbp) deemed extreme

    num_columns = len(analysis_table.columns)
    col_width = f"{100/(num_columns + 1)}%"

    styled_analysis_table = (
        analysis_table
            .style
                .apply(data_reporting_blood_pressure.style_row, axis=1)
                .set_properties(**{'text-align': 'center'})
                .set_table_styles(
                    [
                        {"selector": "th", "props": [
                            ("text-align", "center"),
                            ("padding", "10px"),
                            ("border", "1px solid gray"),
                            ("width", col_width)  # Column headers
                        ]},
                        {"selector": "td", "props": [
                            ("padding", "8px"),
                            ("border", "1px solid gray"),
                            ("width", col_width)
                        ]},  # Data cells
                        {"selector": "table", "props": [
                            ("border-collapse", "collapse"),
                            ("width", "100%"),
                            ("table-layout", "fixed")
                        ]},  # Full width, fixed layout
                    ]
                )
    )

    rounded_analysis_table = styled_analysis_table.format(lambda x: f"{x:.1f}" if isinstance(x, float) else x)

    styled_extremes_table = (
        extremes.style
            .hide(axis='index')
            .set_table_styles(
                [
                    {"selector": "table", "props": [
                        ("border-collapse", "collapse"),
                        ("width", "100% !important"),  # Set table to 100% width
                        ("table-layout", "fixed")  # Prevents content from shrinking table
                    ]},
                    {"selector": "th, td", "props": [
                                        ("border", "1px solid gray"),
                                        ("padding", "10px"),
                                        ("width", "auto"),  # Allow cells to expand naturally
                                        ("white-space", "normal"),  # Allows text wrapping
                                        ("word-wrap", "break-word")  # Ensures long text wraps
                                    ]},
                    {"selector": "th", "props": [("text-align", "center")]}  # Center header text
                ]
            )
    )

    rounded_extremes_table = styled_extremes_table.format(lambda x: f"{x:.1f}" if isinstance(x, float) else x)

    # Prepare html + json variables to send to "Blood Pressure" tab
    analysis_html = rounded_analysis_table.to_html(classes="")

    if extremes.empty:
        extremes_html = "<h1 class='w-full text-center py-20'>No extreme measurement values recorded.</h1>"
    else:
        extremes_html = rounded_extremes_table.to_html(classes="table table-striped")

    analysis_json = analysis_table.to_json()
    extremes_json = extremes.to_json()

    # distribution_html = data_reporting_blood_pressure.get_time_distribution_graph()

    return jsonify({
        "analysis_html": analysis_html,
        "extremes_html": extremes_html,
        "analysis_json": analysis_json,
        "extremes_json": extremes_json,
        "summary_stats": summary_stats,
        # "distribution_html": distribution_html
    })

@iframe_healthie_provider_tab_bp_analysis_bp.route('/healthie/iframe_provider_tab/blood_pressure/download', methods=['GET','POST'])
def iframe_healthie_provider_tab_download_bp_pdf():
    """

    This endpoint is linked to the report download button in the Blood Pressure tab.

    """

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # Retrieve patient info from Healthie
    healthie_user = HealthieUser(post_manager.pseudonyms['healthie_user_id'])
    patient_info = healthie_user._patient_information
    first_initial = (patient_info or {}).get("first_name")[0] if (patient_info or {}).get("first_name") else ""
    last_initial = (patient_info or {}).get("last_name")[0] if (patient_info or {}).get("last_name") else ""
    date_str = datetime.now().strftime("%y%m%d")

    # Obtain form variables
    file_name = request.form.get("file-name").strip() or f"{first_initial}{last_initial}-{date_str}"
    analysis = pd.read_json(io.StringIO(request.form.get("analysis_json")))
    extremes = pd.read_json(io.StringIO(request.form.get("extremes_json")))
    include_intro_section_str = request.form.get("include-intro-section", "off")
    include_intro_section = True if include_intro_section_str == "on" else False

    # Retrieve logo path
    logo_filename = "syntrillo_logo.png"
    logo_path = os.path.join(current_app.static_folder, logo_filename)
    if not os.path.exists(logo_path):
        logger.warning(f"Logo not found at {logo_path}; proceeding without logo.")
        logo_path = None

    # Establish connection to BloodPressureAnalysis class
    bp_analysis = BloodPressureAnalysis(post_manager.syntrillo_internal_key)
    summary_stats = bp_analysis.calculate_summary_stats(hide_intervention=True)

    # Generate 5-character nanoid (URL-safe)
    alphabet = string.ascii_letters + string.digits
    nanoid = ''.join(secrets.choice(alphabet) for _ in range(5))
    file_name = f"{file_name}-{nanoid}"

    bp_report_manager = BloodPressureReport(
        logo=None,
        patient_info_dict=patient_info,
        summary_dict=summary_stats,
        timeframed_df=analysis,
        extremes_df=extremes,
        report_code=nanoid
    )
    # bp_pdf = bp_report_manager.generate_pdf_report()

    if include_intro_section:
        bp_pdf = bp_report_manager.generate_provider_pdf_report()
    else:
        bp_pdf = bp_report_manager.generate_patient_pdf_report()

    return send_file(bp_pdf, as_attachment=True, download_name=f"{file_name}.pdf", mimetype="application/pdf")

@iframe_healthie_provider_tab_bp_analysis_bp.route('/healthie/iframe_provider_tab/blood_pressure/metrics', methods=['GET','POST'])
def iframe_healthie_provider_tab_get_metrics():

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    lookup_codes_manager = LookUpCodesManagement()
    entry = lookup_codes_manager.retrieve_entry_by_internal_key(post_manager.syntrillo_internal_key)

    # Deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # Establish connection to PatientResponses class
    # patient_responses = PatientResponses(post_manager.syntrillo_internal_key)

    # Retrieve exercise and bmi data
    # exercise = patient_responses.get_exercise()

    biometrics = get_biometric_data(post_manager.syntrillo_internal_key)
    bmi = calculate_bmi(biometrics['weight'], biometrics['height'])

    # print(f"-------- biometrics: {biometrics}")

    db_manager = SyntrilloDatabaseManager(post_manager.syntrillo_internal_key)

    # Retrieve heart rate measurements
    healthie_data = get_srs_healthie_data(entry['healthie_user_id'], db_manager, post_manager.syntrillo_internal_key)
    hr_measurements = {
        'baseline_rhr': healthie_data['average_rhr_baseline'],
        'trailing_rhr': healthie_data['average_rhr_trailing'],
    }


    # print(f"-------- hr_measurements: {hr_measurements}")

    secrets = LocalEnvironmentAndSecrets(
        load_healthie_secrets=True,
    )

    if secrets.is_production():
        custom_module_form_id = "2455490"
    else:
        custom_module_form_id = "2203381"

    forms_manager = HealthieForms()
    autoscored_sections  = forms_manager.get_autoscored_sections(
        custom_module_form_id=custom_module_form_id,
        user_id=entry['healthie_user_id'],
    )

    logger.info(f"autoscored_sections: {autoscored_sections}")

    ssq_score = autoscored_sections['formAnswerGroups'][0]['autoscored_sections'] if autoscored_sections and len(autoscored_sections['formAnswerGroups']) > 0 else None

    return jsonify({
        'ssq_score': ssq_score,
        'bmi': bmi,
        'hr_measurements': hr_measurements,
    })


@iframe_healthie_provider_tab_bp_analysis_bp.route('/healthie/iframe_provider_tab/blood_pressure/hr', methods=['GET','POST'])
def iframe_healthie_provider_tab_get_hr_data():
    """
    This endpoint is used to retrieve heart rate data for a patient.

    NOTE: Currently this endpoint is only used for RHR data but should be expanded to include all heart rate data
    when requested in a future feature.
    """

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)
    syntrillo_internal_key = post_manager.syntrillo_internal_key

    lookup_codes_manager = LookUpCodesManagement()
    entry = lookup_codes_manager.retrieve_entry_by_internal_key(syntrillo_internal_key)

    healthie_user_id = entry['healthie_user_id']

    # Get baseline (first 2 weeks), prior (2 weeks before current), and current (latest 2 weeks) RHR data
    healthie_utils = HealthieUtils()
    rhr_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category=RHR_CATEGORY)
    pulse_data = get_healthie_metric_data(healthie_utils, healthie_user_id, category="Pulse")

    hr_data = rhr_data if len(rhr_data) >= len(pulse_data) else pulse_data

    hr_metadata = calc_rhr_metadata(
        rhr_data=hr_data,
        baseline_num_weeks=2,
        trailing_num_weeks=2,
        prior_num_weeks= 2
    ) if hr_data else {}

    return jsonify({
        'average_rhr_baseline': hr_metadata.get('average_rhr_baseline'),
        'average_rhr_trailing': hr_metadata.get('average_rhr_trailing'),
        'average_rhr_prior': hr_metadata.get('average_rhr_prior'),
        "baseline_start_date": hr_metadata.get('baseline_start_date'),
        "baseline_end_date": hr_metadata.get('baseline_end_date'),
        "prior_start_date": hr_metadata.get('prior_start_date'),
        "prior_end_date": hr_metadata.get('prior_end_date'),
        "current_start_date": hr_metadata.get('current_start_date'),
        "current_end_date": hr_metadata.get('current_end_date'),
    })


@iframe_healthie_provider_tab_bp_analysis_bp.route('/healthie/iframe_provider_tab/blood_pressure/biometrics', methods=['GET','POST'])
def iframe_healthie_provider_tab_get_biometrics_data():
    """
    This endpoint is used to retrieve biometrics data for a patient.

    NOTE: Currently this endpoint is only used for BMI, Sodium, and Physical Activity data but should be expanded to include all biometrics data
    when requested in a future feature.
    """

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)
    syntrillo_internal_key = post_manager.syntrillo_internal_key
    lookup_codes_manager = LookUpCodesManagement()
    entry = lookup_codes_manager.retrieve_entry_by_internal_key(syntrillo_internal_key)
    healthie_user_id = entry['healthie_user_id']
    db_manager = SyntrilloDatabaseManager(syntrillo_internal_key)
    healthie_utils = HealthieUtils()

    # I believe that charting is no longer used for physical activity capture (9/8/25)
    # module_id_inactivity_charting = physical_activity_module_ids["module_id_inactivity_charting"]
    # module_id_activity_charting = physical_activity_module_ids["module_id_activity_charting"]

    # physical_activity_module_ids = get_healthie_activity_and_inactivity_module_ids(db_manager=db_manager)
    # module_id_inactivity_intake = physical_activity_module_ids["module_id_inactivity_intake"]
    # module_id_activity_intake = physical_activity_module_ids["module_id_activity_intake"]

    # inactivity_data = db_manager.get_all_patient_form_responses_by_module_id(module_id_inactivity_intake, syntrillo_internal_key)
    # activity_data = db_manager.get_all_patient_form_responses_by_module_id(module_id_activity_intake, syntrillo_internal_key)

    # inactivity_baseline, inactivity_prior, inactivity_current = None, None, None
    # # Need minimum of 3 responses for baseline, prior, and current
    # if inactivity_data and len(inactivity_data) >= 3:
    #     inactivity_baseline, inactivity_prior, inactivity_current = inactivity_data[-1], inactivity_data[1], inactivity_data[0]
    # elif inactivity_data and len(inactivity_data) == 2:
    #     inactivity_baseline, inactivity_current = inactivity_data[-1], inactivity_data[0]
    # elif inactivity_data and len(inactivity_data) == 1:
    #     inactivity_baseline = inactivity_data[0]
    # else:
    #     logger.warning("Patient does not have at least 1 inactivity response...")


    # activity_baseline, activity_prior, activity_current = None, None, None
    # # Need minimum of 3 responses for baseline, prior, and current
    # if activity_data and len(activity_data) >= 3:
    #     activity_baseline, activity_prior, activity_current = activity_data[-1], activity_data[1], activity_data[0]
    # elif activity_data and len(activity_data) == 2:
    #     activity_baseline, activity_current = activity_data[-1], activity_data[0]
    # elif activity_data and len(activity_data) == 1:
    #     activity_baseline = activity_data[0]
    # else:
    #     logger.warning("Patient does not have at least 1 activity response...")


    physical_activity_form_id, physical_activity_module_id = db_manager.get_form_module_ids_by_module_label("activity_questionnaire_intake")
    inactivity_form_id, inactivity_module_id = db_manager.get_form_module_ids_by_module_label("inactivity_questionnaire_intake")

    activity_form_responses = HealthieForms().get_form_answers(
        user_id=healthie_user_id,
        custom_module_form_id=physical_activity_form_id,
    )

    activity_module_ids = [physical_activity_module_id, inactivity_module_id]
    activity_form_responses_list = activity_form_responses.get('formAnswerGroups', []) if activity_form_responses else []

    activity_baseline, activity_prior, activity_current = None, None, None
    inactivity_baseline, inactivity_prior, inactivity_current = None, None, None

    if len(activity_form_responses_list) > 0:
        activity_form_responses_list_cleaned = [
            {
                'created_at': response['created_at'],
                'activity_minutes': next(
                    (answer['answer'] for answer in response['form_answers']
                    if answer['custom_module_id'] == str(physical_activity_module_id)),
                    None
                ),
                'inactivity_hours': next(
                    (answer['answer'] for answer in response['form_answers']
                    if answer['custom_module_id'] == str(inactivity_module_id)),
                    None
                )
            }
            for response in activity_form_responses_list
        ]
        print("============= activity_form_responses_list:", activity_form_responses_list)
        print("============= activity_form_responses_list_cleaned:", activity_form_responses_list_cleaned)
        # Need minimum of 3 responses for baseline, prior, and current
        if len(activity_form_responses_list_cleaned) >= 3:
            activity_baseline = (activity_form_responses_list_cleaned[-1]['activity_minutes'], activity_form_responses_list_cleaned[-1]['created_at'])
            activity_prior = activity_form_responses_list_cleaned[-2]['activity_minutes'], activity_form_responses_list_cleaned[-2]['created_at']
            activity_current = activity_form_responses_list_cleaned[0]['activity_minutes'], activity_form_responses_list_cleaned[0]['created_at']

            inactivity_baseline = (activity_form_responses_list_cleaned[-1]['inactivity_hours'], activity_form_responses_list_cleaned[-1]['created_at'])
            inactivity_prior = (activity_form_responses_list_cleaned[-2]['inactivity_hours'], activity_form_responses_list_cleaned[-2]['created_at'])
            inactivity_current = (activity_form_responses_list_cleaned[0]['inactivity_hours'], activity_form_responses_list_cleaned[0]['created_at'])

        elif len(activity_form_responses_list_cleaned) == 2:
            activity_baseline = (activity_form_responses_list_cleaned[-1]['activity_minutes'], activity_form_responses_list_cleaned[-1]['created_at'])
            activity_prior = None
            activity_current = (activity_form_responses_list_cleaned[0]['activity_minutes'], activity_form_responses_list_cleaned[0]['created_at'])

            inactivity_baseline = (activity_form_responses_list_cleaned[-1]['inactivity_hours'], activity_form_responses_list_cleaned[-1]['created_at'])
            inactivity_prior = None
            inactivity_current = (activity_form_responses_list_cleaned[0]['inactivity_hours'], activity_form_responses_list_cleaned[0]['created_at'])

        elif len(activity_form_responses_list_cleaned) == 1:
            activity_baseline = (activity_form_responses_list_cleaned[-1]['activity_minutes'], activity_form_responses_list_cleaned[-1]['created_at'])
            activity_prior = None
            activity_current = None

            inactivity_baseline = (activity_form_responses_list_cleaned[-1]['inactivity_hours'], activity_form_responses_list_cleaned[-1]['created_at'])
            inactivity_prior = None
            inactivity_current = None

    physical_activity_data = {
        "inactive": {
            "inactivity_baseline": inactivity_baseline,
            "inactivity_prior": inactivity_prior,
            "inactivity_current": inactivity_current
        },
        "active": {
            "activity_baseline": activity_baseline,
            "activity_prior": activity_prior,
            "activity_current": activity_current
        }
    }

    # Get BMI data
    # 1.) get height (from patient info)
    patient_data = get_patient_info(healthie_user_id=healthie_user_id)
    height = patient_data.get("height", None)
    # 2.) get historical weight (from healthie metrics)
    weight_data_response = get_healthie_metric_data(healthie_utils, healthie_user_id, category=WEIGHT_CATEGORY)
    bmis = []
    for weight_data in weight_data_response:
        # 3.) calc bmi similar to PA
        bmis.append({
            'bmi': calculate_bmi(weight_data["metric_stat"], height),
            'date': weight_data["created_at"]
        })
        activity_baseline, activity_prior, activity_current = None, None, None

    # Need minimum of 3 responses for baseline, prior, and current
    # bmis are sorted in ascending order by date.
    bmi_baseline, bmi_prior, bmi_current = None, None, None
    if len(bmis) >= 3:
        bmi_baseline, bmi_prior, bmi_current = bmis[0], bmis[-2], bmis[-1]
    elif len(bmis) == 2:
        bmi_baseline, bmi_current = bmis[0], bmis[-1]
    elif len(bmis) == 1:
        bmi_baseline = bmis[0]
    else:
        logger.warning("Patient does not have at least 1 bmi available...")

    bmi_data = {
        "bmi_current": bmi_current,
        "bmi_prior": bmi_prior,
        "bmi_baseline": bmi_baseline
    }

    # Get Sodium Data
    secrets = LocalEnvironmentAndSecrets(load_healthie_secrets=True)
    if secrets.is_production():
        custom_module_form_id = "2455490"
    else:
        custom_module_form_id = "2203381"

    forms_manager = HealthieForms()
    autoscored_sections  = forms_manager.get_autoscored_sections(custom_module_form_id=custom_module_form_id,user_id=entry['healthie_user_id'])

    ssq_baseline, ssq_prior, ssq_current = None, None, None
    ssq_baseline_date, ssq_prior_date, ssq_current_date = None, None, None
    # Need minimum of 3 responses for baseline, prior, and current
    is_valid_autosections = autoscored_sections and len(autoscored_sections['formAnswerGroups']) > 0
    if is_valid_autosections:
        # SSQ responses are sorted in descending order (first=newest, last=oldest)
        ssq_responses = autoscored_sections['formAnswerGroups']
        if len(ssq_responses) >= 3:
            ssq_baseline = ssq_responses[-1]['autoscored_sections'][-1].get('value', None)
            ssq_baseline_date = ssq_responses[-1].get('created_at', None)
            ssq_prior = ssq_responses[1]['autoscored_sections'][-1].get('value', None)
            ssq_prior_date = ssq_responses[1].get('created_at', None)
            ssq_current = ssq_responses[0]['autoscored_sections'][-1].get('value', None)
            ssq_current_date = ssq_responses[0].get('created_at', None)
        elif len(ssq_responses) == 2:
            ssq_baseline = ssq_responses[-1]['autoscored_sections'][-1].get('value', None)
            ssq_baseline_date = ssq_responses[-1].get('created_at', None)
            ssq_current = ssq_responses[0]['autoscored_sections'][-1].get('value', None)
            ssq_current_date = ssq_responses[0].get('created_at', None)
        elif len(ssq_responses) == 1:
            ssq_baseline = ssq_responses[-1]['autoscored_sections'][-1].get('value', None)
            ssq_baseline_date = ssq_responses[-1].get('created_at', None)
        else:
            logger.warning("Patient does not have at least 1 activity response...")

    ssq_data = {
        "ssq_current": ssq_current,
        "ssq_prior": ssq_prior,
        "ssq_baseline": ssq_baseline,
        "ssq_baseline_date": ssq_baseline_date,
        "ssq_prior_date": ssq_prior_date,
        "ssq_current_date": ssq_current_date
    }


    return jsonify({
        "physical_activity_data":physical_activity_data,
        "bmi_data": bmi_data,
        "ssq_data": ssq_data
    })
