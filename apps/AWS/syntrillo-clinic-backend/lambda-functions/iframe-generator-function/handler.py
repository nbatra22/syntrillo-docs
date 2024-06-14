import json
import awsgi

from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.pseudonyms_management.temporary_lookup_codes_management import TemporaryLookUpCodesManagement

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

from routes.healthie.iframe_provider_tab.devices import iframe_healthie_provider_tab_devices_bp
app.register_blueprint(iframe_healthie_provider_tab_devices_bp)

@app.route('/iframe_healthie_provider_tab')
def iframe_healthie_provider_tab_index():
    healthie_user_id = "1035117"

    # create internal key
    look_up_codes_management = LookUpCodesManagement()
    look_up_codes_management.create_entry(healthie_user_id=healthie_user_id)
    entry = look_up_codes_management.retrieve_entry_by_healthie_user_id(healthie_user_id)
    syntrillo_internal_key = entry['syntrillo_internal_key']

    # create temp code
    temporary_lookup_codes_management = TemporaryLookUpCodesManagement()
    temporary_lookup_code = temporary_lookup_codes_management.create_temporary_pseudo_code(
        syntrillo_internal_key=syntrillo_internal_key,
        purpose=TemporaryLookUpCodesManagement.PURPOSE_HEALTHIE_IFRAME
    )
    
    return render_template("healthie/iframe_provider_tab/index.html",
                            temporary_lookup_code=temporary_lookup_code,
                            iframe_healthie_provider_tab_devices_url = '/prod' + url_for("iframe_healthie_provider_tab_devices_bp.iframe_healthie_provider_tab_devices")
                           )

def handler(event, context):
    print(event)
    print(json.dumps(event))
    return awsgi.response(app, event, context)