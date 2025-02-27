from flask import Blueprint, render_template, request, jsonify, current_app, abort, Response, send_file
import pandas as pd
import json

from .post_management import PostManager
from syntrillo.remote_monitoring.data_reporting_combined import DataReportingCombination
from syntrillo.remote_monitoring.data_reporting_medication_adherence import DataReportingMedicationAdherence
from syntrillo.remote_monitoring.data_reporting_blood_pressure import DataReportingBloodPressure
from syntrillo.bp_analysis.bp_analysis import BloodPressureAnalysis
from syntrillo.remote_monitoring.data_reporting_heart_rate import DataReportingHeartRate
from syntrillo.remote_monitoring.data_reporting_steps import DataReportingSteps
from syntrillo.data_structures.healthie_dataset_handler import DataStructureHealthieDatasetHandler

from syntrillo.api_healthie.medications import HealthieMedications

from syntrillo.system.iframe_validator import IframeValidator

iframe_healthie_provider_tab_bp_analysis = Blueprint('iframe_healthie_provider_tab_bp_analysis', __name__)

from syntrillo.system.logger import logger

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

@iframe_healthie_provider_tab_bp_analysis.route('/healthie/iframe_provider_tab/blood_pressure', methods=['GET','POST'])
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

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # Deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # Establish connection to BloodPressureAnalysis class
    data_reporting_blood_pressure = BloodPressureAnalysis(post_manager.syntrillo_internal_key)

    # Get all available blood pressure data
    _, log = data_reporting_blood_pressure.get_blood_pressure_dataframe(
        start_date=None,
        end_date=None,
    )

    # Confirm blood pressure data is pulled
    if log['success'] == False:
        return jsonify({'html': 'Internal error: Unable to obtain blood pressure dataframe' })

    # Generate analysis + extremes table using BloodPressureAnalysis class methods
    metadata = data_reporting_blood_pressure.calculate_metadata() # Used to calculate since baseline columns; calculates row values since baseline
    timeframes = data_reporting_blood_pressure.calculate_timeframes() # Sorts and separates data by Baseline, Prior, & Current, in two week increments
    analysis_table = data_reporting_blood_pressure.calculate_analysis() # Calculates row values for each timeframe
    # analysis_table_with_inception = data_reporting_blood_pressure.calculate_since_baseline(metadata, analysis_table) # Appends 3 additional columns for lifetime calculations
    extremes = data_reporting_blood_pressure.calculate_extremes() # Returns table for all rows (timestamp, sbp, dbp) deemed extreme
    styled_analysis_table = (
        analysis_table
            .style
                .apply(data_reporting_blood_pressure.style_row, axis=1)
                .set_properties(**{'text-align': 'center'})
                .set_table_styles(
                    [
                        {"selector": "th", "props": [("text-align", "center"),
                                                    ("padding", "10px"),
                                                    ("border", "1px solid gray")]},  # Column headers

                        {"selector": "td", "props": [("padding", "8px"),
                                                    ("border", "1px solid gray")]},  # Data cells

                        {"selector": "table", "props": [("border-collapse", "collapse")]}  # Ensure borders collapse properly
                    ]
                )
    )

    analysis_html = styled_analysis_table.format(lambda x: f"{x:.2f}" if isinstance(x, float) else x).to_html()


    # Prepare html + json variables to send to "Blood Pressure" tab
    # analysis_html = styled_analysis_table.to_html(classes="")
    # analysis_html = analysis_table_with_inception.to_html(classes="table table-striped text-sm text-center")


    analysis_json = analysis_table.to_json()
    # analysis_json = analysis_table_with_inception.to_json()
    extremes_json = extremes.to_json()

    return render_template(
        'healthie/iframe_provider_tab/blood_pressure.html',
        analysis_html=analysis_html,
        analysis_json=analysis_json,
        extremes_json=extremes_json
    )

@iframe_healthie_provider_tab_bp_analysis.route('/healthie/iframe_provider_tab/blood_pressure/download', methods=['GET','POST'])
def iframe_healthie_provider_tab_download_bp_pdf():
    """

    This endpoint is linked to the report download button in the Blood Pressure tab.

    """
    # Obtain the json strings from url params
    analysis_json = request.args.get('analysis_json')
    extremes_json = request.args.get('extremes_json')

    if not analysis_json or not extremes_json:
        return "Error, Insufficient data received", 400

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # Deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # Establish connection to BloodPressureAnalysis class
    data_reporting_blood_pressure = BloodPressureAnalysis(post_manager.syntrillo_internal_key)

    # Convert json variables to dataframes and send to generate_pdf class method
    analysis_df = pd.read_json(analysis_json)
    extremes_df = pd.read_json(extremes_json)
    bp_pdf = data_reporting_blood_pressure.generate_pdf(analysis=analysis_df, extremes=extremes_df)

    return send_file(bp_pdf, as_attachment=True, download_name="BP-report.pdf", mimetype="application/pdf")
