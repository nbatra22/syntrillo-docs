# Path: ./apps/PythonAnywhere/website/healthie/iframe_provider_tab/index.py
from flask import Blueprint, render_template

iframe_healthie_provider_tab_index_bp = Blueprint('iframe_healthie_provider_tab_index', __name__)

@iframe_healthie_provider_tab_index_bp.route('/iframe_healthie_provider_tab_index')
def iframe_healthie_provider_tab_index():
    return render_template('healthie/iframe_provider_tab/index.html')

