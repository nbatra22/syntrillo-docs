# Path: ./apps/PythonAnywhere/website/tests_ui/tab1.py
from flask import Blueprint, render_template

tab1_bp = Blueprint('tests_ui__tab1', __name__)

@tab1_bp.route('/tests_ui/tab1')
def tests_ui_tab1_content():
    return render_template('tests_ui/tab1.html')
