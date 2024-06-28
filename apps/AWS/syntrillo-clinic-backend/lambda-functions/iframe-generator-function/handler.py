import json
import awsgi

from aws_lambda_powertools import Logger
logger = Logger(service="IFRAME_GENERATOR")

from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement

from aws_xray_sdk.core import patch_all, xray_recorder
patch_all()

from flask import (
    Flask,
    jsonify,
    render_template,
    url_for
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("main_page.html")

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

@app.route('/iframe_healthie_provider_tab')
@xray_recorder.capture('iframe_healthie_provider_tab_index')
def iframe_healthie_provider_tab_index():
    healthie_user_id = "1035117"

    # create internal key
    look_up_codes_management = LookUpCodesManagement()
    look_up_codes_management.create_entry(healthie_user_id=healthie_user_id)
    entry = look_up_codes_management.retrieve_entry_by_healthie_user_id(healthie_user_id)
    syntrillo_internal_key = entry['syntrillo_internal_key']

    # print(f"IFrameGeneratorFunction - /iframe_healthie_provider_tab - New Syntrillo Patient ID Created {syntrillo_internal_key}, for Healthie Client {healthie_user_id}" )

    # create temp code
    temporary_lookup_codes_management = TemporaryLookUpCodesManagement()
    temporary_lookup_code = temporary_lookup_codes_management.create_temporary_pseudo_code(
        syntrillo_internal_key=syntrillo_internal_key,
        purpose=TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME
    )

    # print(f"IFrameGeneratorFunction - /iframe_healthie_provider_tab - New Syntrillo Patient Temporary ID Created {temporary_lookup_code}" )
    
    return render_template("healthie/iframe_provider_tab/index.html",
                            temporary_lookup_code=temporary_lookup_code,
                            iframe_healthie_provider_tab_devices = '/prod' + url_for("iframe_healthie_provider_tab_devices_bp.iframe_healthie_provider_tab_devices")
                           )

@logger.inject_lambda_context
def handler(event, context):
    logger.info(f"[IFRAME GENERATOR FUNCTION] <STARTED>")
    return awsgi.response(app, event, context)