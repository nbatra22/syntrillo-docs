# Path: ./apps/PythonAnywhere/website/flask_app.py

import os
from math import isnan

from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecretsNoCache

from flask import Flask, render_template, abort

app = Flask(__name__)

# =================== tests - Only available on specified machines ==========================

if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_') or os.uname().nodename == 'maxwell':

    # app.config["DEBUG"] = True

    # ----------- misc stuff --------------------
    from misc import api_misc
    app.register_blueprint(api_misc)

    # ----------- tests api --------------------
    # routes
    from api import api_bp

    # Register blueprints
    app.register_blueprint(api_bp)

    # ---------- tests ui ---------------------
    from tests_ui.index import tests_ui_index_bp
    from tests_ui.tab1 import tests_ui_tab1_bp
    from tests_ui.tab2 import tests_ui_tab2_bp

    app.register_blueprint(tests_ui_index_bp)
    app.register_blueprint(tests_ui_tab1_bp)
    app.register_blueprint(tests_ui_tab2_bp)

# ================= Healthie Routes and Blueprints ===========================

# ----------- provider tab ---------------------
from routes.healthie.iframe_provider_tab.index import iframe_healthie_provider_tab_index_bp
from routes.healthie.iframe_provider_tab.blood_pressure import iframe_healthie_provider_tab_bp_analysis_bp
from routes.healthie.iframe_provider_tab.forms import iframe_healthie_provider_tab_forms_bp
from routes.healthie.iframe_provider_tab.risk_score import iframe_healthie_provider_tab_risk_score_bp
from routes.healthie.iframe_provider_tab.medications import iframe_healthie_provider_tab_medications_bp
from routes.healthie.iframe_provider_tab.devices import iframe_healthie_provider_tab_devices_bp
from routes.healthie.iframe_provider_tab.status import iframe_healthie_provider_tab_status_bp
from routes.healthie.iframe_provider_tab.onboarding import iframe_healthie_provider_tab_onboarding_bp
from routes.healthie.iframe_provider_tab.care_plan import iframe_healthie_provider_tab_care_plan_bp
from routes.healthie.iframe_provider_tab.cdss import iframe_healthie_provider_tab_cdss_bp
from routes.healthie.iframe_provider_tab.system import iframe_healthie_provider_tab_system_bp
from routes.healthie.iframe_provider_tab.system_devices import iframe_healthie_provider_tab_system_devices_bp
from routes.healthie.iframe_provider_tab.study_outcomes import iframe_healthie_provider_tab_study_outcomes_bp

app.register_blueprint(iframe_healthie_provider_tab_index_bp)
app.register_blueprint(iframe_healthie_provider_tab_bp_analysis_bp)
app.register_blueprint(iframe_healthie_provider_tab_forms_bp)
app.register_blueprint(iframe_healthie_provider_tab_risk_score_bp)
app.register_blueprint(iframe_healthie_provider_tab_medications_bp)
app.register_blueprint(iframe_healthie_provider_tab_devices_bp)
app.register_blueprint(iframe_healthie_provider_tab_status_bp)
app.register_blueprint(iframe_healthie_provider_tab_onboarding_bp)
app.register_blueprint(iframe_healthie_provider_tab_care_plan_bp)
app.register_blueprint(iframe_healthie_provider_tab_cdss_bp)
app.register_blueprint(iframe_healthie_provider_tab_system_bp)
app.register_blueprint(iframe_healthie_provider_tab_system_devices_bp)
app.register_blueprint(iframe_healthie_provider_tab_study_outcomes_bp)

# ----------- provider sidebar ---------------------
from routes.healthie.iframe_provider_sidebar.index import iframe_healthie_provider_sidebar_index_bp
from routes.healthie.iframe_provider_sidebar.billing import iframe_healthie_provider_sidebar_billing_bp
from routes.healthie.iframe_provider_sidebar.status import iframe_healthie_provider_sidebar_status_bp
from routes.healthie.iframe_provider_sidebar.questionnaire import iframe_healthie_provider_sidebar_questionnaire_bp
from routes.healthie.iframe_provider_sidebar.questionnaire_database import iframe_healthie_provider_sidebar_questionnaire_database_bp
from routes.healthie.iframe_provider_sidebar.dumps import iframe_healthie_provider_sidebar_dumps_bp
from routes.healthie.iframe_provider_sidebar.system import iframe_healthie_provider_sidebar_system_bp

app.register_blueprint(iframe_healthie_provider_sidebar_index_bp)
app.register_blueprint(iframe_healthie_provider_sidebar_billing_bp)
app.register_blueprint(iframe_healthie_provider_sidebar_status_bp)
app.register_blueprint(iframe_healthie_provider_sidebar_questionnaire_bp)
app.register_blueprint(iframe_healthie_provider_sidebar_questionnaire_database_bp)
app.register_blueprint(iframe_healthie_provider_sidebar_dumps_bp)
app.register_blueprint(iframe_healthie_provider_sidebar_system_bp)

# ----------- patient sidebar ---------------------
from routes.healthie.iframe_patient_sidebar.index import iframe_healthie_patient_sidebar_bp

app.register_blueprint(iframe_healthie_patient_sidebar_bp)

# ==================================================================================================================
# Jinja2 filters

@app.template_filter('none_string_data_filter')
def none_string_data_filter(value, precision, none_string='no data'):
    """
    Used to format data in Jinja2 templates.

    None values are converted to a space. Strings are returned as is. Numbers are rounded to the specified precision.

    Args:
        value: the value to format
        precision: the number of decimal places to round to

    Returns:
        The formatted value
    """
    if value is None or (isinstance(value, float) and isnan(value)):
        return none_string
    elif isinstance(value, str):
        return value
    else:
        if precision == 0:
            return int(value)
        else:
            return round(value, precision)


# ==================================================================================================================

# default web site
@app.route("/")
def index():
    if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_') or os.uname().nodename == 'maxwell':
        return render_template("main_page.html")
    else:
        return abort(403, description="Access Denied")
