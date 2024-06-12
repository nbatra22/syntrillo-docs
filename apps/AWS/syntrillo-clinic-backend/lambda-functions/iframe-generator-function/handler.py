import json
import awsgi

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
    return render_template("healthie/iframe_provider_tab/index.html",
                            iframe_healthie_provider_tab_devices_url = '/prod' + url_for("iframe_healthie_provider_tab_devices_bp.iframe_healthie_provider_tab_devices_olemaitre")
                           )

def handler(event, context):
    print(event)
    print(json.dumps(event))
    return awsgi.response(app, event, context)