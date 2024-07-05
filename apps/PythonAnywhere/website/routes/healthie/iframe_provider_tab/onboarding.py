# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_tab/onboarding.py
from flask import Blueprint, render_template, request, jsonify

from .post_management import PostManager

from syntrillo.patient_onboarding.manager import PatientOnboardingManager
from syntrillo.charting_note_prefill.handler import ChartingNotePrefillHandler

iframe_healthie_provider_tab_onboarding_bp = Blueprint('iframe_healthie_provider_tab_onboarding_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_tab_onboarding_bp.route('/healthie/iframe_provider_tab/onboarding', methods=['POST'])
def iframe_healthie_provider_tab_onboarding():
    """
    This endpoint is used to display the onboarding page in the provider tab iframe.
    It is called by the healthie_iframe_provider_tab index.html
    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_index_post(request)

    # deal with patients not registered at Syntrillo
    if post_manager.patient_not_registered_at_syntrillo:
        return render_template('healthie/iframe_provider_tab/patient_not_registered.html')

    # --------------------------------------------------------------------
    # Onboarding Manager
    onboarding_manager = PatientOnboardingManager()
    patient_status = onboarding_manager.get_user_status(user_id=post_manager.pseudonyms['healthie_user_id'])
    inconsistencies = onboarding_manager.get_inconsistencies(user_id=post_manager.pseudonyms['healthie_user_id'])

    # --------------------------------------------------------------------
    # Charting Note Prefill
    charting_note_prefill_handler = ChartingNotePrefillHandler(healthie_user_id=post_manager.pseudonyms['healthie_user_id'])
    private_folders_and_documents, _ = charting_note_prefill_handler.list_private_folders_and_documents()
    charting_notes, _ = charting_note_prefill_handler.get_charting_notes()

    return render_template('healthie/iframe_provider_tab/onboarding.html',
                           temporary_lookup_code=post_manager.temporary_lookup_code,
                           patient_status=patient_status,
                           inconsistencies=inconsistencies,
                           private_folders_and_documents=private_folders_and_documents,
                           charting_notes=charting_notes
                           )


# ========================= ENDPOINTS ==========================

@iframe_healthie_provider_tab_onboarding_bp.route('/healthie/iframe_provider_tab/onboarding/healthie_onboarding_generate_personalized_form', methods=['POST'])
def healthie_onboarding_generate_personalized_form():
    """


    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # --------------------------------------------------------------------

    # Convert send_request_to_patient to a boolean
    send_request_to_patient = request.form.to_dict().get('send_request_to_patient')
    send_request_to_patient_bool = send_request_to_patient.lower() in ['on', 'true'] if send_request_to_patient else False

    # new instance of onboarding_manager
    onboarding_manager = PatientOnboardingManager()

    new_form = onboarding_manager.build_personalized_intake_form(
        user_id=post_manager.pseudonyms['healthie_user_id'],
        send_completion_request=send_request_to_patient_bool
    )

    # return status
    if new_form is None:
        log = {
            "success": False,
            "message": "Error: Personalized Intake Form not generated",
            'new_form': None
        }
    else:
        log = {
            "success": True,
            "message": "Personalized Intake Form generated successfully",
            'new_form': new_form
        }

    return jsonify( log ), 200

@iframe_healthie_provider_tab_onboarding_bp.route('/healthie/iframe_provider_tab/onboarding/healthie_prefill_charting_note_form', methods=['POST'])
def healthie_prefill_charting_note_form():
    """


    """

    # get all pseudonyms from post temporary identifier
    post_manager = PostManager()
    post_manager.get_pseudonyms_from_tab_post(request)

    # --------------------------------------------------------------------

    charting_note_prefill_handler = ChartingNotePrefillHandler(healthie_user_id=post_manager.pseudonyms['healthie_user_id'])

    log = charting_note_prefill_handler.run_prefill_ai_agent()

    return jsonify( log ), 200

