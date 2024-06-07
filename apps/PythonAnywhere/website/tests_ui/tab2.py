# Path: ./apps/PythonAnywhere/website/tests_ui/tab2.py
from flask import Blueprint, render_template

tests_ui_tab2_bp = Blueprint('tests_ui_tab2', __name__)

@tests_ui_tab2_bp.route('/tests_ui/tab2_content')
def tests_ui_tab2_content():
    return render_template('tests_ui/tab2.html')