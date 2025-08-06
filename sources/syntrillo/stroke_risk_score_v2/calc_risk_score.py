from agg_data import aggregate_data

def calculate_risk_score(syntrillo_internal_key):
    agg_data = aggregate_data(syntrillo_internal_key)
    tenovi_data = agg_data['tenovi_data']
    srs_form_responses = agg_data['srs_form_responses']

    # Calculate risk score
    # 1. BMI
    # 2. Resting HR
    # 3. Systolic BP
    # 4. Diastolic BP
    # 5. HRV
    # 6. Smoking