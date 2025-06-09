# Path: ./apps/PythonAnywhere/website/routes/healthie/iframe_provider_sidebar/status.py
from flask import Blueprint, render_template, request, jsonify, abort

# python.analysis.extraPaths added into .vscode/settings.json
from syntrillo.system.iframe_validator import IframeValidator
from syntrillo.billing.billing_manager import BillingManager

iframe_healthie_provider_sidebar_billing_bp = Blueprint('iframe_healthie_provider_sidebar_billing_bp', __name__)

# ========================= HTML PAGE ==========================

@iframe_healthie_provider_sidebar_billing_bp.route('/healthie/iframe_provider_sidebar/billing', methods=['POST'])
def iframe_healthie_provider_sidebar_billing():
    """
    This endpoint is used to display the status page in the provider billing iframe.
    It is called by the healthie_iframe_provider_billing index.html

    TODO:
        - retrieve list of patients List[Dict{}]
            - name
            - billing eligibility (bp + calling) # later ?
            - device training bool (healthie)

    """

    # --------------------------------------------------------------------
    # Check if the request origin/referer is allowed
    iframe_validator = IframeValidator()
    iframe_valid, iframe_log = iframe_validator.is_request_allowed(request)
    if not iframe_valid:
        abort(403, description="Access Denied")

    # --------------------------------------------------------------------
    healthie_provider_id = request.form.get('healthie_provider_id')

    # --------------------------------------------------------------------

    # Create an instance of HealthieAPI with the provided API key and organization
    # utils_api = HealthieUtils()

    # Example: Get organization details
    # organization_details = utils_api.get_organization_details()

    return render_template(
        'healthie/iframe_provider_sidebar/billing.html',
        # healthie_provider_id=healthie_provider_id,
        # organization_details=organization_details,
    )

# ========================= ENDPOINTS ==========================

# Retrieval patient specific blood pressure measurements
@iframe_healthie_provider_sidebar_billing_bp.route('/healthie/iframe_provider_billing/bp_data', methods=['GET'])
def iframe_healthie_provider_billing_get_bp_data():
    """
    Returns:
        List of BP objs
    """
    billing_manager = BillingManager()
    all_patient_data = billing_manager.get_all_patient_data()

    '''
    Example output:
    {
        "all_patient_data": [
            {
                "id": 1234567890,
                "name": "John Doe",
                "bp_device_training_status": True,
                "bp_data": ["2021-01-01", "2021-01-02", ..., "2021-01-03"],
                "billing_information": ["2021-01-01", "2021-01-02", ..., "2021-01-03"],
                "is_eligible_for_billing": True
            },
            {
                "id": 1234567890,
                "name": "John Doe",
                "bp_device_training_status": True,
                "bp_data": ["2021-01-01", "2021-01-02", ..., "2021-01-03"],
                "billing_information": ["2021-01-01", "2021-01-02", ..., "2021-01-03"],
                "is_eligible_for_billing": True
            },
            .....
        ]
    }
    '''

    return jsonify({
        "all_patient_data": all_patient_data
    })


