# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/care_plan.py
from flask import Blueprint, render_template, request

iframe_healthie_provider_tab_care_plan_bp = Blueprint('iframe_healthie_provider_tab_care_plan_bp', __name__)

@iframe_healthie_provider_tab_care_plan_bp.route('/healthie/iframe_provider_tab/care_plan', methods=['POST'])
def iframe_healthie_provider_tab_care_plan():
    # Retrieve the form data from the POST request
    #   : these are passed from the healthie_iframe_provider_tab index.html
    #   : healthie_user_id, is None, unless in panic mode
    healthie_provider_id = request.form.get('healthie_provider_id')
    healthie_user_id = request.form.get('healthie_user_id')
    temporary_lookup_code = request.form.get('temporary_lookup_code')

    return render_template('healthie/iframe_provider_tab/care_plan.html')

