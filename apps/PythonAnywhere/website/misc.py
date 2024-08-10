# Path: ./apps/PythonAnywhere/website/misc.py
"""
Non Healthie routes - Can be disregarded in AWS

"""

import os
import statsmodels.api as sm
import markdown2
from flask import Blueprint, render_template, request, jsonify


api_misc = Blueprint('misc', __name__)

# -------------------------
@api_misc.route('/doc')
def serve_markdown_doc():
    # Get the absolute path of the currently running script
    current_dir = os.path.dirname(__file__)

    # Provide the path to your Markdown file in the static folder
    markdown_path = current_dir + '/static/doc.md'

    # Read the content of the Markdown file
    with open(markdown_path, 'r') as file:
        markdown_content = file.read()

    # Convert Markdown to HTML
    html_content = markdown2.markdown(markdown_content)

    # Render the HTML template
    return render_template('markdown_template.html',
                           page_title='doc',
                           content=html_content
                           )

# -------------------------
# Power Analysis HTML page
@api_misc.route('/power')
def power_analysis_page():
    return render_template('power_analysis.html')

# ==================================================================================================================
# POWER CALCULATION

def find_sample_sizes_for_power(
    p1,
    p2,
    desired_power,
    alpha=0.05,
    max_iterations=100,
    ratio=1,
    n1_start=50,
    n2_forced=0
    ):
    # starting values
    n1 = n1_start
    if n2_forced == 0 :
        n2 = n1 * ratio
    else:
        n2 = n2_forced
        ratio = n2 / n1
    iterations = 0

    while True:
        iterations += 1

        # Calculate the effect size (difference in proportions)
        effect_size = sm.stats.proportion_effectsize(p1, p2)

        # Calculate power
        actual_power = sm.stats.tt_ind_solve_power(effect_size, nobs1=n1, ratio=ratio, alpha=alpha, alternative='two-sided')


        # If we're close to the desired power or above max iteration, stop iterating
        if actual_power >= desired_power or iterations >= max_iterations:
            break

        # Sample size adjustments based on the difference in power
        size_adjust = round((desired_power - actual_power) * n1 + 0.5)

        n1 += size_adjust
        if n2_forced == 0 :
            n2 = n1 * ratio
        else:
            n2 = n2_forced
            ratio = n2 / n1

    return {
        'p1': p1,
        'p2': p2,
        'alpha': alpha,
        'ratio': ratio,
        'n1': round(n1),
        'n2': round(n2),
        'n': round(n1) + round(n2),
        'achieved_power': actual_power,
        'iterations': iterations
    }


# -------------------------
# used in this google sheet :
# https://docs.google.com/spreadsheets/d/1rqhqPsPwFM2Dt6IHhf0ETWPfeApq0gWjPtNUuIQ1mBI/edit?usp=drive_link
@api_misc.route('/power-fisher', methods=['POST'])
def power_fisher():

    try:
        data = request.get_json()

        # Extract data from the incoming JSON
        p1 = float(data['p1'])
        p2 = float(data['p2'])
        desired_power = float(data['desired_power'])
        alpha = float(data['alpha'])
        ratio = float(data['ratio'])
        n1_start = int(data['n1_start'])
        n2_forced = float(data['n2_forced'])

        # Run power analysis
        result = find_sample_sizes_for_power(p1=p1, p2=p2, desired_power=desired_power, alpha=alpha, ratio=ratio, n1_start=n1_start, n2_forced=n2_forced)

        # Return results
        return jsonify(result)

    except Exception as e:
        # Log the exception
        print("Error:", str(e))
        return jsonify({'error': str(e), 'data': data })

# -------------------------
# this runs in the console
#  : unit testing
if __name__ == '__main__':
    print('hello')
    result = find_sample_sizes_for_power(p1=0.40, p2=0.55, desired_power=0.80)
    print(result)

