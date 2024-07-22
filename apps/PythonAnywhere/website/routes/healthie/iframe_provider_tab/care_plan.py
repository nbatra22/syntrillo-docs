# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_tab/care_plan.py
from flask import Blueprint, render_template, request, jsonify

import json

from .post_management import PostManager
from syntrillo.remote_monitoring.data_reporting_combined import DataReportingCombination
from syntrillo.remote_monitoring.data_reporting_medication_adherence import DataReportingMedicationAdherence
from syntrillo.remote_monitoring.data_reporting_blood_pressure import DataReportingBloodPressure
from syntrillo.remote_monitoring.data_reporting_heart_rate import DataReportingHeartRate
from syntrillo.data_structures.healthie_dataset_handler import DataStructureHealthieDatasetHandler

iframe_healthie_provider_tab_care_plan_bp = Blueprint('iframe_healthie_provider_tab_care_plan_bp', __name__)

@iframe_healthie_provider_tab_care_plan_bp.route('/healthie/iframe_provider_tab/care_plan', methods=['POST'])
def iframe_healthie_provider_tab_care_plan():
    """
    This endpoint is used to display the care plan page in the provider tab iframe.
    It is called by the healthie_iframe_provider_tab index.html
    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_index_post(request)

    # deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')


    # --------------------------------------------------------------------
    # Summary
    drc = DataReportingCombination(post_manager.syntrillo_internal_key)

    drc.alpha = 0.4

    drc.select_sources_and_obtain_data(blood_pressure=True, heart_rate=True)

    log = drc.select_date_ranges(
        start_date=None,
        end_date=None,
        period='monthly',
        last_ranges_unit='week',
        use_total=False,
        add_whole_range=True,
        whole_period_name='Whole Period',
    )

    summary_df, log = drc.get_summary_statistics()

    # Convert DataFrame to list of dictionaries
    if summary_df.empty:
        summary_data = None
    else:
        summary_data = summary_df.to_dict(orient='records')

    # --------------------------------------------------------------------
    # Medication Adherence data

    # expectations
    healthie_dataset_handler = DataStructureHealthieDatasetHandler('tenovi_pillbox_expectations')
    tenovi_pillbox_expectations_dataset, _ = healthie_dataset_handler.get_patient_data(post_manager.syntrillo_internal_key, full_variable_names=False)

    # monitoring data
    data_reporting_medical_adherence = DataReportingMedicationAdherence(post_manager.syntrillo_internal_key)
    medication_adherence_data, _ = data_reporting_medical_adherence.pillbox_global_report(expected_pattern='twice daily')

    # --------------------------------------------------------------------
    # Heart Rate moments and stats

    data_reporting_heart_rate = DataReportingHeartRate(post_manager.syntrillo_internal_key)

    # ---
    # Pulse
    _, log1 = data_reporting_heart_rate.get_pulse_dataframe()
    _, log2 = data_reporting_heart_rate.get_irregular_heartbeat_dataframe()

    if log1['success'] == False:
        pulse_moments = None
    else:
        # moments
        pulse_moments = data_reporting_heart_rate.get_pulse_moments()

    # ---
    # Heart rate statistics
    _, log = data_reporting_heart_rate.get_heart_rate_statistics_dataframe()

    if log['success'] == False:
        rmssd = None
    else:
        rmssd = data_reporting_heart_rate.get_rmssd()


    # --------------------------------------------------------------------
    # Render the template
    return render_template(
        'healthie/iframe_provider_tab/care_plan.html',
        summary_data=summary_data,
        tenovi_pillbox_expectations_dataset=tenovi_pillbox_expectations_dataset,
        medication_adherence_data=medication_adherence_data,
        pulse_moments=pulse_moments,
        rmssd=rmssd,
        )

# ========================= ENDPOINTS ==========================

def _checkbox_to_bool(checkbox):
    if checkbox is None:
        return False
    else:
        return True

@iframe_healthie_provider_tab_care_plan_bp.route('/healthie/iframe_provider_tab/care_plan/get_blood_pressure_plot', methods=['POST'])
def get_blood_pressure_plot():
    """
    This endpoint return the blood pressure plot as html or json

    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # --------------------------------------------------------------------

    # ---
    # get type of return to generate
    json_or_html = request.form.get('json_or_html')

    # must be 'html' or 'json'
    if json_or_html not in ['html', 'json', 'both']:
        return jsonify({'html': 'Internal error: must be json or html or both' })

    # ---
    # Get the data and generate plot
    data_reporting_blood_pressure = DataReportingBloodPressure(post_manager.syntrillo_internal_key)

    # get all available data
    _, log = data_reporting_blood_pressure.get_blood_pressure_dataframe(
        start_date=None,
        end_date=None,
    )

    # if no data, return None
    # if data, return the plot as html or json as requested
    if log['success'] == False:
        json_returned = None
        html_returned = 'No data'
    else:
        _, html_returned, json_returned = data_reporting_blood_pressure.get_blood_pressure_plotly(representation=json_or_html)

    return jsonify({'json': json_returned, 'html': html_returned })



@iframe_healthie_provider_tab_care_plan_bp.route('/healthie/iframe_provider_tab/care_plan/get_pulse_plot', methods=['POST'])
def get_pulse_plot():
    """
    This endpoint returns the pulse plot as html or json
    It includes also irregular heartbeat data

    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # --------------------------------------------------------------------

    # ---
    # get type of return to generate
    json_or_html = request.form.get('json_or_html')

    # must be 'html' or 'json'
    if json_or_html not in ['html', 'json', 'both']:
        return jsonify({'html': 'Internal error: must be json or html or both' })

    # ---
    # Get the data and generate plot

    data_reporting_heart_rate = DataReportingHeartRate(post_manager.syntrillo_internal_key)

    # ---
    # Get pulse and irregular heartbeat for the plot
    #  : get all available data

    _, log1 = data_reporting_heart_rate.get_pulse_dataframe(
        start_date=None,
        end_date=None,
    )
    _, log2 = data_reporting_heart_rate.get_irregular_heartbeat_dataframe(
        start_date=None,
        end_date=None,
    )

    # if no data, return None
    # if data, return the plot as html or json as requested
    if log1['success'] == False and log2['success'] == False:
        json_returned = None
        html_returned = 'No data'
    else:
        _, html_returned, json_returned = data_reporting_heart_rate.get_pulse_plotly(representation=json_or_html)

    return jsonify({'json': json_returned, 'html': html_returned })



@iframe_healthie_provider_tab_care_plan_bp.route('/healthie/iframe_provider_tab/care_plan/get_heart_rate_statistics_plot', methods=['POST'])
def get_heart_rate_statistics_plot():
    """
    This endpoint returns the heart rate statistics plot as html or json

    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # --------------------------------------------------------------------

    # ---
    # get type of return to generate
    json_or_html = request.form.get('json_or_html')

    # must be 'html' or 'json'
    if json_or_html not in ['html', 'json', 'both']:
        return jsonify({'html': 'Internal error: must be json or html or both' })

    # ---
    # Get the data and generate plot

    data_reporting_heart_rate = DataReportingHeartRate(post_manager.syntrillo_internal_key)

    # get all available data
    _, log = data_reporting_heart_rate.get_heart_rate_statistics_dataframe(
        start_date=None,
        end_date=None,
    )

    # if no data, return None
    # if data, return the plot as html or json as requested
    if log['success'] == False:
        json_returned = None
        html_returned = 'No data'
    else:
        _, html_returned, json_returned = data_reporting_heart_rate.get_heart_rate_statistics_plotly(representation=json_or_html)

    return jsonify({'json': json_returned, 'html': html_returned })



