# Path: ./apps/PythonAnywhere/website/tests_ui/index.py
from flask import Blueprint, render_template

tests_ui_index_bp = Blueprint('tests_ui_index', __name__)

@tests_ui_index_bp.route('/tests_ui/index')
def tests_ui_index():
    return render_template('tests_ui/index.html')
