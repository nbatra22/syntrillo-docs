# Path: ./apps/PythonAnywhere/website/flask_app.py

import os
from math import isnan

from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecretsNoCache

from flask import Flask, render_template, abort

app = Flask(__name__)

# =================== Initialiaze chatbot ==========================

# Register your SQLAlchemy instance with your Flask app
from syntrillo.chatbots.after_hours.models import db

env_secrets = LocalEnvironmentAndSecretsNoCache(load_aws_database_secrets=True)

db_host = env_secrets.get_aws_database_host()
db_user = env_secrets.get_aws_database_user()
db_password = env_secrets.get_aws_database_password()
db_name = os.getenv('DB_NAME', 'syntrillo$ChatbotsInformation')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}?ssl_ca=syntrillo/system/rds-certificate-bundle/us-east-1-bundle.pem'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
with app.app_context():
    db.create_all() 

# # =================== tests - Only available on specified machines ==========================

# if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_') or os.uname().nodename == 'maxwell':

#     # app.config["DEBUG"] = True

#     # ----------- misc stuff --------------------
#     from misc import api_misc
#     app.register_blueprint(api_misc)

#     # ----------- tests api --------------------
#     # routes
#     from api import api_bp

#     # Register blueprints
#     app.register_blueprint(api_bp)

#     # ---------- tests ui ---------------------
#     from tests_ui.index import tests_ui_index_bp
#     from tests_ui.tab1 import tests_ui_tab1_bp
#     from tests_ui.tab2 import tests_ui_tab2_bp

#     app.register_blueprint(tests_ui_index_bp)
#     app.register_blueprint(tests_ui_tab1_bp)
#     app.register_blueprint(tests_ui_tab2_bp)

# # ================== Healthie route for webhook endpoints ========================

from routes.healthie.endpoints import healthie_endpoint_bp

app.register_blueprint(healthie_endpoint_bp)

# # ================= Healthie Routes and Blueprints ===========================

# # ----------- provider tab ---------------------
# from routes.healthie.iframe_provider_tab.index import iframe_healthie_provider_tab_index_bp
# from routes.healthie.iframe_provider_tab.status import iframe_healthie_provider_tab_status_bp
# from routes.healthie.iframe_provider_tab.devices import iframe_healthie_provider_tab_devices_bp
# from routes.healthie.iframe_provider_tab.onboarding import iframe_healthie_provider_tab_onboarding_bp
# from routes.healthie.iframe_provider_tab.care_plan import iframe_healthie_provider_tab_care_plan_bp
# from routes.healthie.iframe_provider_tab.cdss import iframe_healthie_provider_tab_cdss_bp
# from routes.healthie.iframe_provider_tab.system import iframe_healthie_provider_tab_system_bp
# from routes.healthie.iframe_provider_tab.system_devices import iframe_healthie_provider_tab_system_devices_bp

# app.register_blueprint(iframe_healthie_provider_tab_index_bp)
# app.register_blueprint(iframe_healthie_provider_tab_status_bp)
# app.register_blueprint(iframe_healthie_provider_tab_devices_bp)
# app.register_blueprint(iframe_healthie_provider_tab_onboarding_bp)
# app.register_blueprint(iframe_healthie_provider_tab_care_plan_bp)
# app.register_blueprint(iframe_healthie_provider_tab_cdss_bp)
# app.register_blueprint(iframe_healthie_provider_tab_system_bp)
# app.register_blueprint(iframe_healthie_provider_tab_system_devices_bp)

# # ----------- provider sidebar ---------------------
# from routes.healthie.iframe_provider_sidebar.index import iframe_healthie_provider_sidebar_index_bp
# from routes.healthie.iframe_provider_sidebar.status import iframe_healthie_provider_sidebar_status_bp
# from routes.healthie.iframe_provider_sidebar.questionnaire import iframe_healthie_provider_sidebar_questionnaire_bp
# from routes.healthie.iframe_provider_sidebar.questionnaire_database import iframe_healthie_provider_sidebar_questionnaire_database_bp
# from routes.healthie.iframe_provider_sidebar.dumps import iframe_healthie_provider_sidebar_dumps_bp
# from routes.healthie.iframe_provider_sidebar.system import iframe_healthie_provider_sidebar_system_bp

# app.register_blueprint(iframe_healthie_provider_sidebar_index_bp)
# app.register_blueprint(iframe_healthie_provider_sidebar_status_bp)
# app.register_blueprint(iframe_healthie_provider_sidebar_questionnaire_bp)
# app.register_blueprint(iframe_healthie_provider_sidebar_questionnaire_database_bp)
# app.register_blueprint(iframe_healthie_provider_sidebar_dumps_bp)
# app.register_blueprint(iframe_healthie_provider_sidebar_system_bp)

# # ----------- patient sidebar ---------------------
# from routes.healthie.iframe_patient_sidebar.index import iframe_healthie_patient_sidebar_bp

# app.register_blueprint(iframe_healthie_patient_sidebar_bp)

# # ==================================================================================================================
# # Jinja2 filters

# @app.template_filter('none_string_data_filter')
# def none_string_data_filter(value, precision, none_string='no data'):
#     """
#     Used to format data in Jinja2 templates.

#     None values are converted to a space. Strings are returned as is. Numbers are rounded to the specified precision.

#     Args:
#         value: the value to format
#         precision: the number of decimal places to round to

#     Returns:
#         The formatted value
#     """
#     if value is None or (isinstance(value, float) and isnan(value)):
#         return none_string
#     elif isinstance(value, str):
#         return value
#     else:
#         if precision == 0:
#             return int(value)
#         else:
#             return round(value, precision)


# # ==================================================================================================================

# # default web site
# @app.route("/")
# def index():
#     if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_') or os.uname().nodename == 'maxwell':
#         return render_template("main_page.html")
#     else:
#         return abort(403, description="Access Denied")






