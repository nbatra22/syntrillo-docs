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
    This endpoint is used to display blood pressure analysis table and a pdf download,
    which is called by the healthie_iframe_provider_tab index.html.

    The pdf can be viewed in sources/bp_analysis/reports.
    """
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        abort(403, description="Access Denied")

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # --------------------------------------------------------------------

    # ---
    # Get the data and generate plot
    data_reporting_blood_pressure = BloodPressureAnalysis(post_manager.syntrillo_internal_key)

    # Get all available data
    _, log = data_reporting_blood_pressure.get_blood_pressure_dataframe(
        start_date=None,
        end_date=None,
    )

    # If no data, return None
    # If data, return the plot as html or json as requested
    if log['success'] == False:
        return jsonify({'html': 'Internal error: Unable to obtain blood pressure dataframe' })

    # Check if pdf is required (for download button)
    is_pdf = request.form.get('pdf')

    metadata = data_reporting_blood_pressure.calculate_metadata()
    timeframes = data_reporting_blood_pressure.calculate_timeframes()
    analysis_table = data_reporting_blood_pressure.calculate_analysis()
    analysis_table_with_inception = data_reporting_blood_pressure.calculate_since_baseline(metadata, analysis_table)
    extremes = data_reporting_blood_pressure.calculate_extremes()

    # if is_pdf == True:
    #     # Convert rendered HTML to PDF
    #     bp_analysis_pdf = data_reporting_blood_pressure.generate_pdf(analysis_table_with_inception, extremes)

    #     # Return the PDF for download
    #     return send_file(bp_analysis_pdf, as_attachment=True, download_name="blood-pressure-report.pdf")

    analysis_html = analysis_table_with_inception.to_html(classes="table table-striped")
    analysis_json = analysis_table_with_inception.to_json()
    extremes_json = extremes.to_json()

    return render_template(
        'healthie/iframe_provider_tab/blood_pressure.html',
        analysis_html=analysis_html,
        analysis_json=analysis_json,
        extremes_json=extremes_json
    )

@iframe_healthie_provider_tab_bp_analysis.route('/healthie/iframe_provider_tab/blood_pressure/download', methods=['GET','POST'])
def iframe_healthie_provider_tab_download_bp_pdf():
    analysis_json = request.args.get('analysis_json')
    extremes_json = request.args.get('extremes_json')

    if not analysis_json or not extremes_json:
        return "Error, Insufficient data received", 400

    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    data_reporting_blood_pressure = BloodPressureAnalysis(post_manager.syntrillo_internal_key)

    analysis_df = pd.read_json(analysis_json)
    extremes_df = pd.read_json(extremes_json)
    bp_pdf = data_reporting_blood_pressure.generate_pdf(analysis=analysis_df, extremes=extremes_df)

    return send_file(bp_pdf, as_attachment=True, download_name="BP-report.pdf", mimetype="application/pdf")
