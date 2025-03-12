# Select data from 
# - healthie_form_templates 
# - healthie_form_responses

# Examle requests
# select t.form_id, t.form_name, t.module_id, t.module_label, r.syntrillo_internal_key, r.answer  from healthie_form_templates as t join healthie_form_responses as r on t.form_id = r.form_id and t.module_id = r.module_id where r.syntrillo_internal_key = '3261f346-ef09-4311-8a5f-f36d5d67e58d';
# +---------+------------------------------+-----------+-------------------------------------------------------------------------+--------------------------------------+--------------------------------------------------------------------------------------+
# | form_id | form_name                    | module_id | module_label                                                            | syntrillo_internal_key               | answer                                                                               |
# +---------+------------------------------+-----------+-------------------------------------------------------------------------+--------------------------------------+--------------------------------------------------------------------------------------+
# | 1136356 | Stroke Risk Factors Input    | 9798955   | Blood thinner - Prescribed ?                                            | 3261f346-ef09-4311-8a5f-f36d5d67e58d | No                                                                                   |
# +---------+------------------------------+-----------+-------------------------------------------------------------------------+--------------------------------------+--------------------------------------------------------------------------------------+

# Example results (python dictionary)
healthie_forms_answers = [
    {
        "form_id": 1136356,
        "form_name": "Stroke Risk Factors Input",
        "module_id": 9798955,
        "module_label": "Blood thinner - Prescribed ?",
        "syntrillo_internal_key": "3261f346-ef09-4311-8a5f-f36d5d67e58d",
        "answer": 'No'
    }, 
]

# Idea to calculate score directly from the 2 tables (healthie_form_templates, healthie_form_responses)
def fetch_patient_data(syntrillo_internal_key):
    return healthie_forms_answers

def clean_patient_data(data):
    # Cleaning rules have to be defined
    return data

def format_score_input_table(cleaned_patient_data):    
    first_item = cleaned_patient_data[0]
    
    transformed_data = {
        "syntrillo_internal_key": first_item["syntrillo_internal_key"],
        "section_1": [
            {
                "cardioembolic_lines": [
                    {"blood_thinner": first_item["answer"]}
                ]
            }
        ]
    }
    
    return transformed_data

def calculate_score(score_input_table):
    score = 0
    # Go through section 1
    section_1 = score_input_table["section_1"]
    if section_1[0]["cardioembolic_lines"][0]["blood_thinner"] == 'No': score += 6.3

    # Go through section 2
    # ...
    
    return str(score)

if __name__ == "__main__":
    raw_patient_data = fetch_patient_data('3261f346-ef09-4311-8a5f-f36d5d67e58d')
    cleaned_patient_data = clean_patient_data(raw_patient_data)
    score_input_table = format_score_input_table(cleaned_patient_data)
    score = calculate_score(score_input_table)
    print(score)