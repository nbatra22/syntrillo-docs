# ./Syntrillo_Clinic/apps/PythonAnywhere/website/api.py
# used to deliver Stroke Risk Factors to Scoring and Care Plans algorithms

import random
from flask import Blueprint, request, jsonify

api_bp = Blueprint('api', __name__)

# Hardcoded API key for demonstration purposes
API_KEY = 'ABCDEF'

# Dummy patient data
dummy_patients = {
    '123': {
        'age': 50,
        'gender': 'M',
        'SBP': 150,
        'DBP': 85,
        'activity': 100,
        'BMI': 25,
        'HRV': 30,
        'RHR': 70,
        'smoking': 0.5,
        'stroke_etiology': 'Cardioembolic',
        'history': {
            'smoker': 'no',
            'intracranial_atherosclerosis': 'no',
            'AFib': 'no',
            'OSA': 'no',
            'CPAP': {
                'prescribed': 'no',
                'used': 'no',
            }
        },
        'medication': {
            'blood_thinner': 'no',
            'aspirin': 'no',
            'plavix': 'no',
            'other_antiplatelet': 'no',
            'statin': 'no',
            'hypoglycemic_agent': 'no',
            'antihypertensive': 'no',
        },
        'lab': {
            'LDL': 60,
            'HbA1c': 3,
        }
    },
    '456': {
        'age': 50,
        'gender': 'M',
        'SBP': 120,
        'DBP': 70,
        'activity': 100,
        'BMI': 55,
        'HRV': 20,
        'RHR': 60,
        'smoking': 0,
        'stroke_etiology': 'Cardioembolic',
        'history': {
            'smoker': 'no',
            'intracranial_atherosclerosis': 'no',
            'AFib': 'no',
            'OSA': 'no',
            'CPAP': {
                'prescribed': 'no',
                'used': 'no',
            }
        },
        'medication': {
            'blood_thinner': 'yes',
            'aspirin': 'no',
            'plavix': 'no',
            'other_antiplatelet': 'no',
            'statin': 'no',
            'hypoglycemic_agent': 'no',
            'antihypertensive': 'no',
        },
        'lab': {
            'LDL': 60,
            'HbA1c': 3,
        }
    },
    # Add more dummy patient data here as needed
}

def generate_random_patient_data():
    # Define ranges for random values
    age_range = (18, 100)
    sbp_range = (90, 200)
    dbp_range = (50, 120)
    activity_range = (50, 150)
    bmi_range = (15, 40)
    hrv_range = (10, 50)
    rhr_range = (50, 100)
    smoking_prob_range = (0, 1)
    ldl_range = (40, 200)
    hba1c_range = (3, 10)

    # Generate random values for each field
    patient_data = {
        'age': random.randint(*age_range),
        'gender': random.choice(['M', 'F']),
        'SBP': random.randint(*sbp_range),
        'DBP': random.randint(*dbp_range),
        'activity': random.randint(*activity_range),
        'BMI': random.randint(*bmi_range),
        'HRV': random.randint(*hrv_range),
        'RHR': random.randint(*rhr_range),
        'smoking': random.uniform(*smoking_prob_range),
        'stroke_etiology': random.choice(['Cardioembolic', 'Large Vessel', 'Small Vessel', 'Other', 'Cryptogenic']),
        'history': {
            'smoker': random.choice(['yes', 'no']),
            'intracranial_atherosclerosis': random.choice(['yes', 'no']),
            'AFib': random.choice(['yes', 'no']),
            'OSA': random.choice(['yes', 'no']),
            'CPAP': {
                'prescribed': random.choice(['yes', 'no']),
                'used': random.choice(['yes', 'no']),
            }
        },
        'medication': {
            'blood_thinner': random.choice(['yes', 'no']),
            'aspirin': random.choice(['yes', 'no']),
            'plavix': random.choice(['yes', 'no']),
            'other_antiplatelet': random.choice(['yes', 'no']),
            'statin': random.choice(['yes', 'no']),
            'hypoglycemic_agent': random.choice(['yes', 'no']),
            'antihypertensive': random.choice(['yes', 'no']),
        },
        'lab': {
            'LDL': random.randint(*ldl_range),
            'HbA1c': random.randint(*hba1c_range),
        }
    }
    return patient_data

@api_bp.route('/api', methods=['POST'])
def api():
    # Check if the request contains the API key
    if 'api_key' not in request.form or request.form['api_key'] != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401  # Unauthorized

    # Check if the request contains the patient_id
    if 'patient_id' not in request.form:
        return jsonify({'error': 'Patient ID not provided'}), 400  # Bad Request

    patient_id = request.form['patient_id']

    # If the patient_id is 'random', return a random dataset
    if patient_id == 'random':
        return jsonify(generate_random_patient_data())

    # Check if the requested patient exists in the dummy data
    if patient_id not in dummy_patients:
        return jsonify({'error': 'Patient not found'}), 404  # Not Found

    # Return data for the requested patient
    return jsonify(dummy_patients[patient_id])
