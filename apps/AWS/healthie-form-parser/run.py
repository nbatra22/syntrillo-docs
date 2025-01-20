from loguru import logger

from syntrillo_lib.api_healthie.forms import HealthieForms
from syntrillo_lib.api_healthie.user import HealthieUser

def my_pprint(x: dict):
    """
    Print a dictionary in a pretty format
    """
    import json
    logger.info(json.dumps(x, indent=4))


def get_module_info(
    form_id: int,
    module_id   
):
    # logger.info("Hello from healthie-form-parser!")
    # logger.info(f"form_id: {form_id}")
    # logger.info(f"module_id: {module_id}")

    # class to fetch forms form Healthie API
    forms = HealthieForms()

    # Fetch by form_id and module_id
    response = forms.get_form_by_id(form_id)
    # my_pprint(response)
    # TODO: add this logic in the syntrilo-lib
    modules = response['customModuleForm']['custom_modules']
    module = [x for x in modules if x['id'] == module_id]
    my_pprint(module)

    # Get the patient responses
    # response = forms.get_form_answers_group(
    # response = forms.get_form_answers_group_and_modules(
    #     custom_module_form_id=form_id,
    #     # user_id=patient_id
    # )
    # my_pprint(response)
    # breakpoint()


if __name__ == "__main__":
    
    # Investor demo patient
    # patient_id = '1660020'
    # Pau Patient
    patient_id = 2101747

    user = HealthieUser(patient_id)
    my_pprint(user.get_patient_information())

    ids = [
        {'form_id': '1765843', 'module_id': '15159755'}, # name
        {'form_id': '1765843', 'module_id': '15159758'}, # age
        {'form_id': '1373914', 'module_id': '11841977'}, # sex

        # hospital records
        {'form_id': '1765843', 'module_id': '15159774'}, # Systolic BP - Initial
        {'form_id': '1765843', 'module_id': '15159775'}, # Diastolic BP - Initial
        {'form_id': '1765843', 'module_id': '15159780'}, # Resting HR - Initial

        # phq-9 severity of depression
        {'form_id': '1765846', 'module_id': '15159808'}, # Little interest or pleasure in doing things
        {'form_id': '1765846', 'module_id': '15159809'}, # Feeling down, depressed, or hopeless
        {'form_id': '1765846', 'module_id': '15159810'}, # Trouble sleeping
        {'form_id': '1765846', 'module_id': '15159811'}, # Feeling tired or having little energy
        {'form_id': '1765846', 'module_id': '15159812'}, # Poor appetite or overeating
        {'form_id': '1765846', 'module_id': '15159813'}, # Feeling bad about yourself or that you are a failure or have let yourself or your family down
        {'form_id': '1765846', 'module_id': '15159814'}, # Trouble concentrating on things, such as reading the newspaper or watching television
        {'form_id': '1765846', 'module_id': '15159815'}, # Moving or speaking so slowly that other people could have noticed? Or the opposite - being so fidgety or restless that you have been moving around a lot more than usual
        {'form_id': '1765846', 'module_id': '15159816'}, # Thoughts that you would be better off dead or of hurting yourself in some way
    ]
    
    for id in ids:
        get_module_info(
            # patient_id=patient_id,
            form_id=id['form_id'],
            module_id=id['module_id']
        )
