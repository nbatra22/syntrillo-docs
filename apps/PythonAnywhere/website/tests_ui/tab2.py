# Path: ./apps/PythonAnywhere/website/tests_ui/tab2.py
from flask import Blueprint, render_template

tab2_bp = Blueprint('tests_ui__tab2', __name__)

@tab2_bp.route('/tests_ui/tab2')
def tests_ui_tab2_content():
    return render_template('tests_ui/tab2.html')
