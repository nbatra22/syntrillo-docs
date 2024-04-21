import os
import sys
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from healthie.forms import HealthieAPIForms

class HealthieAPIOnboardingManager(HealthieAPIForms):
    """
    A class extending HealthieAPI to handle onboarding operations.

    - define here the onboarding, Healthie-specific, Intake Forms and Charting Notes
       : the rationale to place that here (and not in the data module) is that the data module can be used by other app, with specific data structures

    """

    # static variables. These are custom_module_form.external_id
    forms = [
        "onboarding_clinician",
        "onboarding_nurse",
    ]

    def get_user_status(
        self,
        user_id : str = None
        ):
        """
        Returns a dict with the status of the given user

        """

        patient_status = []

        # loop forms
        for form in self.forms:

            # need custom_module_form_id of custom_module_form.external_id
            #  : there could be several matches
            custom_module_form_ids = self.get_form_id_by_external_id(external_id=form)

            for custom_module_form_id in custom_module_form_ids:
                # then need get_form_answers_group and status
                answers_group_status = self.get_form_answers_group_status(custom_module_form_id=custom_module_form_id, user_id=user_id)

                if answers_group_status and 'formAnswerGroups' in answers_group_status:
                    for group in answers_group_status['formAnswerGroups']:
                        status_entry = {
                            'name': group['name'],
                            'created_at': group['created_at'],
                            'user_id': group['user_id'],
                            'filler_id': group['filler']['id'] if 'filler' in group else 'N/A',
                            'finished': group['finished']
                        }
                        patient_status.append(status_entry)

        return patient_status



if __name__ == "__main__":
    # Example usage of the list_forms function
    dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/.env")
    manager_api = HealthieAPIOnboardingManager(dotenv_path=dotenv_path)

    response = manager_api.get_user_status(user_id="1035117")

    print(json.dumps(response, indent=4))







