from flask import Blueprint, render_template, request, jsonify, current_app, abort, Response, send_file
import pandas as pd
import io
from datetime import datetime

from .post_management import PostManager

from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.stroke_risk_score.responses.patient_responses import PatientResponses
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager

from syntrillo.api_healthie.medications import HealthieMedications
from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.system.iframe_validator import IframeValidator

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
    analysis_table = data_reporting_blood_pressure.get_analysis_table() # Calculates row values for each timeframe
    # analysis_table_with_inception = data_reporting_blood_pressure.calculate_since_baseline(metadata, analysis_table) # Appends 3 additional columns for lifetime calculations
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

    rounded_analysis_table = styled_analysis_table.format(lambda x: f"{x:.2f}" if isinstance(x, float) else x)

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
        # "distribution_html": distribution_html
    })

@iframe_healthie_provider_tab_bp_analysis_bp.route('/healthie/iframe_provider_tab/blood_pressure/download', methods=['GET','POST'])
def iframe_healthie_provider_tab_download_bp_pdf():
    """

    This endpoint is linked to the report download button in the Blood Pressure tab.

    """

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # Obtain form variables
    file_name = request.form.get("file-name").strip() or "BP-report.pdf"
    report_title = request.form.get("report-title") or "Blood Pressure Analysis"
    analysis = pd.read_json(io.StringIO(request.form.get("analysis_json")))
    extremes = pd.read_json(io.StringIO(request.form.get("extremes_json")))

    # Establish connection to BloodPressureAnalysis class
    data_reporting_blood_pressure = BloodPressureAnalysis(post_manager.syntrillo_internal_key)

    bp_pdf = data_reporting_blood_pressure.save_to_pdf(analysis=analysis, extremes=extremes, report_title=report_title)

    return send_file(bp_pdf, as_attachment=True, download_name=f"{file_name}", mimetype="application/pdf")

@iframe_healthie_provider_tab_bp_analysis_bp.route('/healthie/iframe_provider_tab/blood_pressure/metrics', methods=['GET','POST'])
def iframe_healthie_provider_tab_get_metrics():

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # Deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # Establish connection to PatientResponses class
    patient_responses = PatientResponses(post_manager.syntrillo_internal_key)

    # Retrieve exercise and bmi data
    exercise = patient_responses.get_exercise()
    bmi = patient_responses.get_bmi()

    db_manager = SyntrilloDatabaseManager(post_manager.syntrillo_internal_key)

    # Retrieve heart rate measurements
    hr_measurements, log = db_manager.get_latest_measurements(metric_name='pulse', count=3)

    forms_manager = HealthieForms()
    autoscored_sections  = forms_manager.get_autoscored_sections(
        custom_module_form_id=2455490,
        user_id=post_manager.posted_healthie_user_id,
    )

    ssq_score = autoscored_sections.data['formAnswerGroups'][0]['autoscored_sections'] if autoscored_sections and len(autoscored_sections.data['formAnswerGroups']) > 0 else None

    return jsonify({
        'ssq_score': ssq_score,
        'exercise': exercise,
        'bmi': bmi,
        'hr_measurements': hr_measurements,
    })
