# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_tab/care_plan.py
from flask import Blueprint, render_template, request, jsonify

from .post_management import PostManager
from syntrillo.remote_monitoring.data_reporting_medication_adherence import DataReportingMedicationAdherence

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
    # Medication Adherence

    remote_monitoring_data_reporting = DataReportingMedicationAdherence(post_manager.syntrillo_internal_key)

    # get medication adherence data
    medication_adherence_data, log = remote_monitoring_data_reporting.pillbox_global_report(expected_pattern='twice daily')


    # --------------------------------------------------------------------
    # Render the template
    return render_template('healthie/iframe_provider_tab/care_plan.html',
                           medication_adherence_data=medication_adherence_data,
                           )


