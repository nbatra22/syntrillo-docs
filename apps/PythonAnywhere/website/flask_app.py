# Path: ./apps/PythonAnywhere/website/flask_app.py

import os

from flask import Flask, render_template

app = Flask(__name__)

app.config["DEBUG"] = True

# =================== tests - Only available on specified machines ==========================

if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_') or os.uname().nodename == 'maxwell':

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

# ================== Healthie route for webhook endpoints ========================

from routes.healthie.endpoints import healthie_endpoint_bp

app.register_blueprint(healthie_endpoint_bp)

# ================= Healthie Routes and Blueprints ===========================

# ----------- provider tab ---------------------
from routes.healthie.iframe_provider_tab.index import iframe_healthie_provider_tab_index_bp
from routes.healthie.iframe_provider_tab.status import iframe_healthie_provider_tab_status_bp
from routes.healthie.iframe_provider_tab.devices import iframe_healthie_provider_tab_devices_bp
from routes.healthie.iframe_provider_tab.onboarding import iframe_healthie_provider_tab_onboarding_bp
from routes.healthie.iframe_provider_tab.care_plan import iframe_healthie_provider_tab_care_plan_bp
from routes.healthie.iframe_provider_tab.cdss import iframe_healthie_provider_tab_cdss_bp
from routes.healthie.iframe_provider_tab.system import iframe_healthie_provider_tab_system_bp
from routes.healthie.iframe_provider_tab.system_devices import iframe_healthie_provider_tab_system_devices_bp

app.register_blueprint(iframe_healthie_provider_tab_index_bp)
app.register_blueprint(iframe_healthie_provider_tab_status_bp)
app.register_blueprint(iframe_healthie_provider_tab_devices_bp)
app.register_blueprint(iframe_healthie_provider_tab_onboarding_bp)
app.register_blueprint(iframe_healthie_provider_tab_care_plan_bp)
app.register_blueprint(iframe_healthie_provider_tab_cdss_bp)
app.register_blueprint(iframe_healthie_provider_tab_system_bp)
app.register_blueprint(iframe_healthie_provider_tab_system_devices_bp)

# ----------- provider sidebar ---------------------
from routes.healthie.iframe_provider_sidebar.index import iframe_healthie_provider_sidebar_index_bp
from routes.healthie.iframe_provider_sidebar.status import iframe_healthie_provider_sidebar_status_bp
from routes.healthie.iframe_provider_sidebar.questionnaire import iframe_healthie_provider_sidebar_questionnaire_bp
from routes.healthie.iframe_provider_sidebar.system import iframe_healthie_provider_sidebar_system_bp

app.register_blueprint(iframe_healthie_provider_sidebar_index_bp)
app.register_blueprint(iframe_healthie_provider_sidebar_status_bp)
app.register_blueprint(iframe_healthie_provider_sidebar_questionnaire_bp)
app.register_blueprint(iframe_healthie_provider_sidebar_system_bp)

# ----------- patient sidebar ---------------------
from routes.healthie.iframe_patient_sidebar.index import iframe_healthie_patient_sidebar_bp

app.register_blueprint(iframe_healthie_patient_sidebar_bp)


# ==================================================================================================================

# default web site
@app.route("/")
def index():
    if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_') or os.uname().nodename == 'maxwell':
        return render_template("main_page.html")
    else:
        return render_template("blank.html")






