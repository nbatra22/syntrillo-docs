# Path: ./sources/syntrillo/patient_onboarding/manager.py

import json

from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.api_healthie.auth import HealthieAuth
from syntrillo.api_healthie.utils import HealthieUtils
from syntrillo.data_structures.data_structure import DataStructure
from syntrillo.data_structures.storage_manager import StorageManager
from syntrillo.api_healthie.misc import *

class PatientOnboardingManager():
    """
    A class handling onboarding operations.

    - define here the onboarding, Healthie-specific, Intake Forms and Charting Notes
       : the rationale to place that here (and not in the data module) is that the data module can be used by other app, with specific data structures

    """

    # -------------
    # static variables. These are custom_module_form.external_id

    #
    personalized_intake_form = "onboarding_patient_personalized_{user_id}"
    personalized_intake_form_header = "onboarding_patient_personalized_header"
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

    def __init__(self):
        self.auth = HealthieAuth()
        self.forms = HealthieForms()
        self.utils = HealthieUtils()

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
            custom_module_form_ids = self.forms.get_form_id_by_external_id(external_id=form)

            # Is this test necessary ??
            if not custom_module_form_ids:
                # If custom_module_form_ids is empty, append a status with 'form' and 'status' set to null
                form_info = {
                    'form': form,                   # form name
                    'is_intake_form' : None,        # Is it an IntakeForm
                    'completion_request' : None,    # id IntakeForm, was it requested
                    'status': None                  # status of the answers
                }
                patient_status.append(form_info)
                continue

            for custom_module_form_id in custom_module_form_ids:

                # get details of this form
                form_details = self.forms.get_form_by_id(form_id=custom_module_form_id)

                # then need get_form_answers_group and status
                answers_group_status = self.forms.get_form_answers_group_status(custom_module_form_id=custom_module_form_id, user_id=user_id)

                # get completion request if Intake Form
                if form_details['customModuleForm']['use_for_charting'] == False:
                    is_intake_form = True
                    completion_request_status, completion_request_date = self.forms.was_form_completion_requested(user_id=user_id, form_id=custom_module_form_id)
                else:
                    is_intake_form = False
                    completion_request_status = None
                    completion_request_date = None

                # Initialize form information with default values
                form_info = {
                    'form': form,
                    'is_intake_form' : is_intake_form,
                    'completion_request_status' : completion_request_status,
                    'completion_request_date' : completion_request_date,
                    'status': None
                }


                if answers_group_status['formAnswerGroups']:
                    # add all available answers
                    for group in answers_group_status['formAnswerGroups']:
                        # Update form status details
                        form_info['status'] = {
                            'name': group['name'],
                            'created_at': group['created_at'],
                            'user_id': group['user_id'],
                            'filler_id': group['filler']['id'] if 'filler' in group else 'N/A',
                            'finished': group['finished'],
                            'locked_at': group['locked_at'],
                        }

                        # Get modules with missing answers (null or unknown) for the current form
                        modules_with_missing_answers = self.forms.get_modules_with_missing_answers(custom_module_form_id=custom_module_form_id, user_id=user_id)

                        # Add null answer count to the status entry
                        missing_answer_count = sum(module_info['missing_answer_count'] for module_info in modules_with_missing_answers)
                        form_info['status']['missing_answer_count'] = missing_answer_count

                        patient_status.append(form_info)
                else:
                    # append empty entry if form not answered
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

        inconsistencies = []

        # Iterate over unique pairs of forms from forms_discrepancies
        for i in range(len(self.forms_discrepancies)):
            form1 = self.forms_discrepancies[i]
            custom_module_form1_ids = self.forms.get_form_id_by_external_id(external_id=form1)

            for custom_module_form1_id in custom_module_form1_ids:
                # get_form_answers_group with answers
                answers_form1 = self.forms.get_form_answers_group_and_modules(custom_module_form_id=custom_module_form1_id, user_id=user_id)

                for j in range(i + 1, len(self.forms_discrepancies)):  # Start from i + 1 to avoid duplicates
                    form2 = self.forms_discrepancies[j]
                    if form1 != form2 :

                        custom_module_form2_ids = self.forms.get_form_id_by_external_id(external_id=form2)

                        for custom_module_form2_id in custom_module_form2_ids:

                            # get_form_answers_group with answers
                            answers_form2 = self.forms.get_form_answers_group_and_modules(custom_module_form_id=custom_module_form2_id, user_id=user_id)

                            # Compare answers between form1 and form2
                            inconsistencies.extend(self.find_answer_discrepancies(answers_form1, answers_form2))

        return inconsistencies


    def find_answer_discrepancies(self, answers1, answers2):
        """
        Compare answers from two different forms and return discrepancies based on external_id.
        """

        discrepancies = []

        # Extract form answers from both sets of answers
        form_answers1 = self.extract_form_answers(answers1)
        form_answers2 = self.extract_form_answers(answers2)

        # Compare answers and identify discrepancies based on external_id
        for external_id in form_answers1:
            if external_id in form_answers2:
                answer1 = form_answers1[external_id]
                answer2 = form_answers2[external_id]

                # Normalize and order multi-value answers
                normalized_answer1 = self.normalize_multi_value_answer(answer1)
                normalized_answer2 = self.normalize_multi_value_answer(answer2)

                print(repr(answer1), repr(answer2))

                # Check if normalized answers are different
                if normalized_answer1 != normalized_answer2:

                    # report blocking discrepancies
                    #  : null or 'unknown' will not be counted as major discrepancies
                    blocker = False
                    if ( answer1 is not None ) and ( answer2 is not None ) \
                        and (answer1 not in ['unknown']) and (answer2 not in ['unknown']) :
                        blocker = True

                    discrepancy_info = {
                    'external_id': external_id,
                    'answer1': answer1 if answer1 is not None else 'null',  # Handle null
                    'answer2': answer2 if answer2 is not None else 'null',  # Handle null
                    'blocker': blocker,
                    }
                    discrepancies.append(discrepancy_info)

        return discrepancies

    def normalize_multi_value_answer(self, answer):
        """
        Normalize a multi-value answer by splitting, stripping, and sorting the values.
        """
        if answer is None:
            return None

        # Split answer by '\n', strip whitespace, and sort the values
        values = [value.strip() for value in answer.split('\n') if value.strip()]
        normalized_answer = '\n'.join(sorted(values))

        return normalized_answer

    def extract_form_answers(self, answers):
        """
        Extract form answers from the response data using external_id as the key.
        """

        form_answers = {}

        if 'formAnswerGroups' in answers:
            for group in answers['formAnswerGroups']:
                if 'form_answers' in group:
                    for answer in group['form_answers']:
                        if 'custom_module' in answer and 'external_id' in answer['custom_module'] and 'answer' in answer:
                            external_id = answer['custom_module']['external_id']
                            form_answers[external_id] = answer['answer']

        return form_answers


    def build_personalized_intake_form(
        self,
        user_id : str = None,
        send_completion_request : bool = False,
        ):

        """
            Build a personalized Intake Form made of questions having missing answers

            Looks like only the API key owner will see this form.  May need to use the provider API key OR share the form with the provider(s), via their email address
            => TODO: DB of API keys, so that the systemas acts as the provider ???
            => TODO: DB of providers emails is sharing

        """

        custom_modules_with_missing_answer = []
        for form in self.forms_personalized_build:

            custom_module_form_ids = self.forms.get_form_id_by_external_id(external_id=form)

            for custom_module_form_id in custom_module_form_ids:
                missing_answer = self.forms.get_modules_with_missing_answers(
                    custom_module_form_id=custom_module_form_id,
                    user_id=user_id
                )

                custom_modules_with_missing_answer.extend(missing_answer)

        # Remove duplicated modules based on external_id
        unique_custom_modules_with_missing_answer = []
        seen_external_ids = set()

        for module_info in custom_modules_with_missing_answer:
            external_id = module_info['custom_module']['external_id']
            if external_id not in seen_external_ids:
                seen_external_ids.add(external_id)
                unique_custom_modules_with_missing_answer.append(module_info['custom_module'])

        # print(json.dumps(unique_custom_modules_with_missing_answer, indent=4))

        # TODO : *archive* this patient-specific form ASAP (do not delete it)

        # -----------------
        # append to personalized_intake_form_header

        # Load JSON data from StorageManager
        storage_manager = StorageManager()
        data_structure = DataStructure(storage_manager)
        data_structure.load_from_storage(self.personalized_intake_form_header)

        # Transform JSON data to custom_modules
        personalized_intake_form_header_custom_modules = data_structure.transform_for_healthie_api()

        # Combine header modules and unique missing modules
        header_unique_custom_modules_with_missing_answer = personalized_intake_form_header_custom_modules + unique_custom_modules_with_missing_answer

        print(json.dumps(header_unique_custom_modules_with_missing_answer, indent=4))

        # ----------------
        # Build form from unique modules
        # Replace {user_id} placeholder with actual user_id
        external_id = self.personalized_intake_form.format(user_id=user_id)

        # get user name : TODO : compliance with regulations ?
        user_details = self.utils.get_user_from_id(user_id=user_id)

        new_form = self.forms.create_form_wrapper(
            form_name=f"Personalized Intake Form for patient {user_details['first_name']} {user_details['last_name']}",
            modules=header_unique_custom_modules_with_missing_answer,
            use_for_charting=False, # This is an Intake Form
            use_for_program=False,
            external_id=external_id,
            external_id_type="",
            is_video=False,
            # on_completion_ifs_tag_id=on_completion_ifs_tag_id,
            # prefill=prefill,
        )

        if send_completion_request :
            # the form that was just built
            new_form_id = new_form['form_response']['createCustomModuleForm']['customModuleForm']['id']

            new_form_request_payload = self.forms.create_form_completion_request(
                recipient_ids=user_id,
                form=new_form_id,
                is_recurring=False,
            )
        else:
            new_form_request_payload = None

        return { "new_form" : new_form, "new_form_request_payload" : new_form_request_payload }


    # build final form from gaps





if __name__ == "__main__":
    # Example usage of the list_forms function
    dotenv_path = ".env"
    manager_api = PatientOnboardingManager(dotenv_path=dotenv_path)

    if False:
        response = manager_api.get_user_status(user_id="1035117")
        HealthieAuth.print_pretty_json(response)

    if False:
        response = manager_api.get_inconsistencies(user_id="1035117")
        HealthieAuth.print_pretty_json(response)

    if True:
        response = manager_api.build_personalized_intake_form(user_id="1035117")
        HealthieAuth.print_pretty_json(response)











