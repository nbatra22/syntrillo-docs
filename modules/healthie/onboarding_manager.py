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

    # -------------
    # static variables. These are custom_module_form.external_id

    #
    personalized_intake_form = "onboarding_patient_personalized_{user_id}"
    final_onboarding_form = "onboarding_final"

    # forms listed in the status table on the provider tab
    forms_status = [
        "onboarding_clinician",
        "onboarding_nurse",
        personalized_intake_form,
        final_onboarding_form,
    ]

    # forms where the code will look for discrepancies
    forms_discrepancies = [
        "onboarding_clinician",
        "onboarding_nurse",
    ]

    # forms where the code will look for gaps and build the personalized Intake Form
    forms_personalized_build = [
        "onboarding_clinician",
        "onboarding_nurse",
    ]

    # forms used by the code to build the final onboarding charting note
    forms_final_build = [
        "onboarding_clinician",
        "onboarding_nurse",
        personalized_intake_form,
    ]




    # -------------
    def get_user_status(
        self,
        user_id : str = None
        ):
        """
        Returns a dict with the status of the given user

        """

        patient_status = []

        # loop forms
        for unformatted_form in self.forms_status:

            # Replace {user_id} placeholder with actual user_id
            form = unformatted_form.format(user_id=user_id)

            # need custom_module_form_id of custom_module_form.external_id
            #  : there could be several matches
            custom_module_form_ids = self.get_form_id_by_external_id(external_id=form)

            if not custom_module_form_ids:
                # If custom_module_form_ids is empty, append a status with 'form' and 'status' set to null
                form_info = {
                    'form': form,
                    'status': None
                }
                patient_status.append(form_info)
                continue

            for custom_module_form_id in custom_module_form_ids:
                # then need get_form_answers_group and status
                answers_group_status = self.get_form_answers_group_status(custom_module_form_id=custom_module_form_id, user_id=user_id)

                if answers_group_status and 'formAnswerGroups' in answers_group_status:
                    # Initialize form information with default values
                    form_info = {
                        'form': form,
                        'status': None
                    }

                    for group in answers_group_status['formAnswerGroups']:
                        # Update form status details
                        form_info['status'] = {
                            'name': group['name'],
                            'created_at': group['created_at'],
                            'user_id': group['user_id'],
                            'filler_id': group['filler']['id'] if 'filler' in group else 'N/A',
                            'finished': group['finished']
                        }

                        # Get modules with null answers for the current form
                        modules_with_null_answers = self.get_modules_with_null_answers(custom_module_form_id=custom_module_form_id, user_id=user_id)

                        # Add null answer count to the status entry
                        null_answer_count = sum(module_info['null_answer_count'] for module_info in modules_with_null_answers)
                        form_info['status']['null_answer_count'] = null_answer_count

                        patient_status.append(form_info)

        return patient_status


    def get_inconsistencies(
        self,
        user_id : str = None
    ) :
        """
        get inconsistencies between forms listed in forms_discrepancies for this user

        returns a list with internal variable names having different responses


        """
        for form1 in self.forms_discrepancies:
            custom_module_form1_ids = self.get_form_id_by_external_id(external_id=form1)

            for custom_module_form1_id in custom_module_form1_ids:
                # get_form_answers_group with answers
                answers_form1 = self.get_form_answers_group(custom_module_form_id=custom_module_form1_id, user_id=user_id)

                for form2 in self.forms_discrepancies:
                    if form1 != form2 :

                        custom_module_form2_ids = self.get_form_id_by_external_id(external_id=form2)

                        for custom_module_form2_id in custom_module_form2_ids:

                            # get_form_answers_group with answers
                            answers_form2 = self.get_form_answers_group(custom_module_form_id=custom_module_form2_id, user_id=user_id)

                            print(json.dumps(answers_form1, indent=4))
                            print(json.dumps(answers_form2, indent=4))





    # build final from from gaps




if __name__ == "__main__":
    # Example usage of the list_forms function
    dotenv_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/.env")
    manager_api = HealthieAPIOnboardingManager(dotenv_path=dotenv_path)

    if True:
        response = manager_api.get_user_status(user_id="1035117")
        print(json.dumps(response, indent=4))









