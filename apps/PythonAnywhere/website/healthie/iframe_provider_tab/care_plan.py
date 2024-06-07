# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/care_plan.py
from flask import Blueprint, render_template

iframe_healthie_provider_tab_care_plan_bp = Blueprint('iframe_healthie_provider_tab_care_plan_bp', __name__)

@iframe_healthie_provider_tab_care_plan_bp.route('/healthie/iframe_provider_tab/care_plan')
def iframe_healthie_provider_tab_care_plan():
    return render_template('healthie/iframe_provider_tab/care_plan.html')

