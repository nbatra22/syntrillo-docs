# Path: ./sources/syntrillo/data_structures/healthie_dataset_handler.py
import json
import os
import re
import uuid
import pandas as pd
from typing import Tuple

from syntrillo.api_healthie.forms import HealthieForms
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement


class DataStructureHealthieDatasetHandler:
    """
    Retrieves data from Healthie questionnaires derived from data structures stored here.

    Can retrieve single or multiple patients and questionnaires

    TODO : add request for completion ?
    TODO : add json to db ?
    TODO : document external id & type

    """

    form : HealthieForms = None
    lookup_codes : LookUpCodesManagement = None

    def __init__(
        self,
        structure_name: str,
        ) -> None:
        """
        Initializes the class with the structure name.

        The structure name is also the external_id of Healthie's customModuleForm

        Args:
            structure_name: str: The name of the structure to be used.

        """

        self.structure_name = structure_name

        # initialize the form class
        self.form = HealthieForms()
        self.lookup_codes = LookUpCodesManagement()


    def _list_custom_modules(self):
        """
        Lists all the custom modules in Healthie, having our structure name as external_id_type.
        ( external_id includes the version / external_id_type does not: it's the structure name )

        This is useful since we could have several versions of the same structure, and we need to get data from all of them.

        Returns list of customModuleForm ids

        """

        form_ids = self.form.get_form_id_by_external_id(external_id_type=self.structure_name)

        return form_ids

    def get_patient_data(
        self,
        syntrillo_internal_key: uuid.UUID = None,
        full_variable_names: bool = False,
        ) -> Tuple[list, dict]:
        """

        Get data from all Heathie structure_name questionnaires.

        In particular, we get data from all the Healthie formAnswerGroups for the given user having customModuleForm with internal_id = structure_name

        Note : nested queries are not supported by Healthie API, so we need to make multiple queries to get all the data, and we cannot filter queries based on nested data.

        Args:
            syntrillo_internal_key: uuid.UUID: The internal key of the user in Syntrillo.

        Returns a tuple:
           - dataset: list of dictionaries containing the data
           - log: dictionary containing the result of the operation

        """

        log = {
            "success": True,
        }

        if syntrillo_internal_key is None:
            log["success"] = False
            log["error"] = "No syntrillo_internal_key provided"
            return None, log

        # get healthie user id
        entry = self.lookup_codes.retrieve_entry_by_internal_key(syntrillo_internal_key)
        healthie_user_id = entry.get("healthie_user_id", None)

        if healthie_user_id is None:
            log["success"] = False
            log["error"] = "No healthie_user_id found"
            return None, log

        # get list of customModuleForm ids
        form_ids = self._list_custom_modules()

        # get all the formAnswerGroups for the user
        dataset = []
        for custom_module_form_id in form_ids:
            data = self.form.get_form_answers_group_and_modules(
                user_id=healthie_user_id,
                custom_module_form_id=custom_module_form_id
            )
            # print(json.dumps(data, indent=4, default=str))

            # filter the data
            for formAnswerGroup in data['formAnswerGroups']:

                structure_internal_name = formAnswerGroup["custom_module_form"].get("external_id_type", None)
                if structure_internal_name != self.structure_name:
                    log["success"] = False
                    log["error"] = "Internal name mismatch"
                    return None, log


                # get metatada for this datapoint
                datapoint = {
                        "healthie_form_answer_group_id": formAnswerGroup["id"],
                        "name": formAnswerGroup["name"],
                        "created_at": formAnswerGroup["created_at"],
                        "finished": formAnswerGroup["finished"],
                        "locked_at": formAnswerGroup["locked_at"],
                        "locked_by": formAnswerGroup["locked_by"],
                        "structure_internal_name": structure_internal_name,
                        "structure_name_with_version": formAnswerGroup["custom_module_form"].get("name", None),
                    }

                # Extract version number from the 'structure_name_with_version' field
                match = re.search(r'\(v(\d+\.\d+)\)', datapoint["structure_name_with_version"])
                if match:
                    datapoint["version"] = match.group(1)

                # add the filler id (healthie provider id) if it's not the patient
                if formAnswerGroup["custom_module_form"].get("use_for_charting", None) is True:
                    datapoint["filler_healthie_user_id"] = formAnswerGroup["filler"].get("id", None)

                # add all the answers to the datapoint
                for answer in formAnswerGroup["form_answers"]:
                    mod_type = answer.get('custom_module', {}).get('mod_type', None)

                    # add only variables with an answers and an external_id (ie our id)
                    if mod_type not in ['label', 'read_only']:
                        variable = answer.get('custom_module', {}).get('external_id', None)
                        if variable is not None:
                            if full_variable_names:
                                # we define the variable name as the structure_internal_name + the external_id of the custom_module
                                variable = structure_internal_name + '.' + variable

                            # blank aswers are stored as empty strings
                            var_answer = answer.get('answer', '')
                            if var_answer is None:
                                var_answer = ''
                            datapoint[ variable ] = var_answer

                # append datapoint to dataset
                dataset.append(datapoint)

        return dataset, log



if __name__ == "__main__":
    # Test the class
    #  : enrollment_patient_information
    #  : tenovi_pillbox_expectations
    data_structure = DataStructureHealthieDatasetHandler(structure_name="tenovi_pillbox_expectations")

    syntrillo_internal_key = data_structure.lookup_codes.retrieve_entry_by_healthie_user_id(healthie_user_id="1035117").get("syntrillo_internal_key", None)

    dataset, log = data_structure.get_patient_data(syntrillo_internal_key=syntrillo_internal_key)

    print(log)

    print(json.dumps(dataset, indent=4, default=str))








