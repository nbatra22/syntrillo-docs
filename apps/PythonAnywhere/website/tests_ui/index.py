# Path: ./apps/PythonAnywhere/website/tests_ui/index.py
from flask import Blueprint, render_template

index_bp = Blueprint('tests_ui__index', __name__)

@index_bp.route('/tests_ui/index')
def status():
    return render_template('tests_ui/index.html')
