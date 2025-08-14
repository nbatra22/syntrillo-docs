from datetime import datetime

from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.system.logger import logger

from helpers import clean_text
from models import FormResponse, Medication
from syntrillo.api_healthie.utils import HealthieUtils

class FormResponseService:
    def __init__(self):
        self.user_mapping = {}
        self.db_manager = SyntrilloDatabaseManager(syntrillo_internal_key="NOT_USED")
        self.unique_user_ids = set()
        self.PAGE_SIZE = 100

    def process(self) -> None:
        """
        Main processing method that orchestrates:
        1. Fetching form responses from Healthie
        2. Flattening and processing the responses
        3. Processing medications for the users
        """
        try:
            graphql_output = self._fetch_all_form_responses_from_healthie()
            flattened_output = self._flatten_form_responses(graphql_output)

            # Process both form responses and medications
            self._insert_form_responses_to_sql(flattened_output)
            self._process_and_store_medications()

        finally:
            if hasattr(self, 'db_manager'):
                self.db_manager.conn.close()
                logger.info("Database connection closed")

    def _fetch_all_form_responses_from_healthie(self) -> dict:
        """
        Fetches form responses from Healthie API

        Args:
            None
        Returns:
            dict: The JSON response 'data' from the API
        """



        # Set up the GraphQL query to list custom module forms
        graphql_query = '''
            query formAnswerGroups(
                $date: String, # e.g "2021-10-29" using type ISO8601DateTime does not work
                $custom_module_form_id: ID, # e.g "11"
                $page_size: Int, # e.g. "1" or "10" or "100"
                $should_paginate: Boolean # e.g. "true" or "false"
                $after: Cursor # e.g "eyJrIjpbIjIwMjUtMDMtMTRU....."
            ) {
                formAnswerGroups(
                    date: $date,
                    custom_module_form_id: $custom_module_form_id,
                    page_size: $page_size,
                    should_paginate: $should_paginate,
                    after: $after
                ) {
                    name
                    cursor
                    custom_module_form {
                        id
                    }
                    created_at
                    form_answers {
                        label
                        displayed_answer
                        created_at
                        user_id
                        custom_module {
                            id
                        }
                    }
                }
            }
        '''

        # Query output is dict with a single key called "formAnswerGroups"
        # For example:
        # {
        # "formAnswerGroups": [
        #     {
        #         "name": "Telemed - PHQ-9 (v1.0)",
        #         "cursor": "eyJrIjpbIjIwMjUtMDMtMTRUMTU6NDU6MDAuMDAwMDAwWiIsMzUyOTUyMDksIjM1Mjk1MjA5Il19",
        #         "custom_module_form": {
        #             "id": "1765846"
        #         },
        #         "created_at": "2024-12-25 19:23:06 -0500",
        #         "form_answers": [
        #             {
        #                 "label": "Over the last 2 weeks, how often have you been bothered by any of the following problems?",
        #                 "displayed_answer": null,
        #                 "created_at": "2024-12-25 19:23:06 -0500",
        #                 "user_id": "2101747",
        #                 "custom_module": {
        #                     "id": "15159807"
        #                 }
        #             }
        #         ]
        #     }
        # ]
        # }

        # Healthie responses can time out ... pagination is required in this case
        # Healthie PROD servers can hanlde 100 records, not 800+ (500 error)

        logger.info("Fetching form responses from Healthie.")
        try:
            all_form_responses = []
            cursor = None
            has_more_pages = True
            # Continue fetching pages until no more results
            while has_more_pages:

                if cursor:
                    variables = {
                        "page_size": self.PAGE_SIZE,
                        "should_paginate": True,
                        "after": cursor
                    }
                else:
                    variables = {
                        "page_size": self.PAGE_SIZE,
                        "should_paginate": True
                    }
                # Retrieve the current set of responses
                response: dict = HealthieUtils.run_graphql_query(graphql_query, variables)
                current_page_data = response.get("formAnswerGroups", [])

                # Append the newest set of responses to output array
                all_form_responses.extend(current_page_data)


                if len(current_page_data) == self.PAGE_SIZE and current_page_data[-1].get("cursor"):
                    cursor = current_page_data[-1]["cursor"]
                    logger.info(f"Fetched {len(current_page_data)} records. Getting next page with cursor.")
                else:
                    has_more_pages = False
                    logger.info("No more pages to fetch.")

            logger.info(f"Successfully fetched {len(all_form_responses)} form responses.")

            output = {"formAnswerGroups": all_form_responses}
            return output

        except Exception as e:
            logger.error(f"Error fetching form responses from Healthie: {e}")

    def _flatten_form_responses(self, json_data: dict) -> list[FormResponse]:
        """
        Flattens the given `json_data` into a list of FormResponses

        Args:
            json_data (dict): the json data returned from the Healthie's GraphQL API
        Returns:
            list[FormResponse]
        """
        try:
            form_answer_groups = json_data.get("formAnswerGroups", [])

            if not form_answer_groups:
                logger.warning("No form answer groups found in the API response")
                return []

            temp_responses = []

            for form_group in form_answer_groups:
                form_id = form_group.get("custom_module_form", {}).get("id", None)

                for answer in form_group.get("form_answers", []):
                    module_id = answer.get("custom_module", {}).get("id", None)
                    healthie_user_id = answer.get("user_id", None)
                    displayed_answer = clean_text(answer.get("displayed_answer", None))

                    created_at_str = answer.get("created_at", None)
                    try:
                        created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S %z")
                    except (ValueError, TypeError):
                        created_at = datetime.now()

                    if all([module_id, form_id, healthie_user_id]):
                        temp_data = {
                            'form_id': form_id,
                            'module_id': module_id,
                            'healthie_user_id': healthie_user_id,
                            'answer': displayed_answer,
                            'created_at': created_at
                        }
                        temp_responses.append(temp_data)
                        self.unique_user_ids.add(healthie_user_id)

            if not temp_responses:
                return []

            # Get user mappings for all users at once
            if self.unique_user_ids:
                self.user_mapping = self._batch_retrieve_user_mapping(list(self.unique_user_ids))

            # Create final FormResponse objects
            flattened_responses = []
            missing_user_ids = set()

            for response in temp_responses:
                healthie_user_id = response['healthie_user_id']
                if healthie_user_id in self.user_mapping:
                    syntrillo_internal_key = self.user_mapping[healthie_user_id]['syntrillo_internal_key']
                    flattened_response = FormResponse(
                        form_id=response['form_id'],
                        module_id=response['module_id'],
                        syntrillo_internal_key=syntrillo_internal_key,
                        answer=response['answer'],
                        created_at=response['created_at']
                    )
                    flattened_responses.append(flattened_response)
                else:
                    missing_user_ids.add(healthie_user_id)

            if missing_user_ids:
                logger.warning(f"No mapping found for {len(missing_user_ids)} healthie_user_ids: {list(missing_user_ids)[:5]}")

            return flattened_responses

        except Exception as e:
            logger.error(f"Error flattening JSON form responses: {e}")
            return []

    def _batch_retrieve_user_mapping(self, healthie_user_ids: list[int]) -> dict:
        """
        Batch retrieve entries from the user_look_up_codes table using multiple healthie_user_ids.

        Args:
            healthie_user_ids (list): List of healthie user IDs
            db_connection: Database connection object (optional)

        Returns:
            dict: A dictionary mapping healthie_user_ids to their corresponding syntrillo_internal_keys
        """
        if not healthie_user_ids:
            return {}

        try:
            # Initialize the database manager specifically for the user_look_up_codes table
            db_manager = LookUpCodesManagement()
            db_connection = db_manager.conn

            # Create a cursor
            with db_connection.cursor() as cursor:
                # Create placeholders for the IN clause
                placeholders = ', '.join(['%s'] * len(healthie_user_ids))

                select_query = f"""
                    SELECT
                        healthie_user_id,
                        BIN_TO_UUID(syntrillo_internal_key) as syntrillo_internal_key,
                        BIN_TO_UUID(pseudo_code_for_tenovi_phi_access) as pseudo_code_for_tenovi_phi_access
                    FROM user_look_up_codes
                    WHERE healthie_user_id IN ({placeholders});
                """

                cursor.execute(select_query, tuple(healthie_user_ids))
                entries = cursor.fetchall()

                # Create a mapping of healthie_user_id to syntrillo internal key
                user_mapping = {}
                for entry in entries:
                    healthie_user_id = entry[0]
                    user_mapping[healthie_user_id] = {
                        'syntrillo_internal_key':entry[1],
                        'healthie_user_id': healthie_user_id
                    }

                logger.info(f"Retrieved {len(user_mapping)} entries out of {len(healthie_user_ids)} requested")

                return user_mapping

        except Exception as e:
            logger.error(f"Error retrieving user mapping from database: {e}")
            return []

    def _fetch_patient_medications(self) -> list[Medication]:
        """Fetches medications for stored user IDs"""
        graphql_query = '''
            query medications(
                $active: Boolean
                $patient_id: ID
            ) {
                medications(
                    active: $active
                    patient_id: $patient_id
                ) {
                    id
                    name
                    active
                    directions
                    dosage
                    code
                    start_date
                    end_date
                    user_id
                }
            }
        '''

        all_medications = []

        for user_id in self.unique_user_ids:
            variables = {
                "active": True,
                "patient_id": user_id
            }

            try:
                response = HealthieUtils.run_graphql_query(graphql_query, variables)

                if response and "medications" in response:
                    # Convert each medication dict to a Medication model
                    medications = [Medication(**med) for med in response["medications"]]
                    all_medications.extend(medications)

            except Exception as e:
                logger.error(f"Error fetching medications for user {user_id}: {e}")
                continue

        return all_medications

    def _process_and_store_medications(self) -> None:
        """Processes and stores medications for all users"""
        if not self.unique_user_ids:
            logger.warning("No user IDs available for medication processing")
            return

        medications = self._fetch_patient_medications()

        if not medications:
            logger.warning("No medications found")
            return

        medication_records = []
        for med in medications:
            if med.user_id not in self.user_mapping:
                continue

            medication_records.append({
                'syntrillo_internal_key': self.user_mapping[med.user_id]["syntrillo_internal_key"],
                'med_name': med.name,
                'med_dosage': med.dosage,
                'directions': med.directions,
                'compliance': "Unknown"
            })

        self._insert_medications_to_sql(medication_records)

    def _insert_medications_to_sql(self, medication_records: list[dict]) -> None:
        """Inserts medication records into database"""
        if not medication_records:
            return

        db_connection = self.db_manager.conn

        try:
            with db_connection.cursor() as cursor:
                sql_query = """
                    INSERT INTO patient_medications (
                        syntrillo_internal_key,
                        med_name,
                        med_dosage,
                        directions,
                        compliance
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        med_dosage = VALUES(med_dosage),
                        directions = VALUES(directions),
                        compliance = VALUES(compliance)
                """

                # Convert to list of tuples for executemany
                med_records = [
                    (
                        record['syntrillo_internal_key'],
                        record['med_name'],
                        record['med_dosage'],
                        record['directions'],
                        record['compliance']
                    )
                    for record in medication_records
                ]

                cursor.executemany(sql_query, med_records)
                db_connection.commit()

                logger.info(f"Successfully inserted/updated {len(med_records)} medication records")

        except Exception as e:
            logger.error(f"Error inserting medications: {e}")
            raise e

    def _insert_form_responses_to_sql(self, flattened_responses: list[FormResponse]) -> None:
        """
        Saves the given list of FormResponses to Amazon RDS

        Args:
            flattened_responses (list[FormResponse]): the list of FormResponses to be saved
        Returns:
            None: the function does not return anything
        Raises:
            Exception: any type of exception while saving the data
        """

        # TODO: we are reusing this object, which does too many things but helps us move fast
        # Use it when it speeds you up, but don't implement more methods in it
        # This object should allow us to run arbitrary SQL queries against our internal
        # operational Amazon RDS

        if not flattened_responses:
            logger.warning("No responses to insert into database")
            return

        db_connection = self.db_manager.conn

        try:
            with db_connection.cursor() as cursor:
                sql_query = """
                    INSERT INTO healthie_form_responses (
                        form_id,
                        module_id,
                        syntrillo_internal_key,
                        answer,
                        created_at
                    )
                    VALUES (%s, %s, %s,REPLACE(%s, '\n', '|'), %s)
                """

                # Convert to list of tuples for executemany
                response_records = [
                    (
                        response.form_id,
                        response.module_id,
                        response.syntrillo_internal_key,
                        response.answer,
                        response.created_at
                    )
                    for response in flattened_responses
                ]

                # Execute a bulk query with tuples
                cursor.executemany(sql_query, response_records)
                db_connection.commit()

                logger.info(f"Successfully inserted or updated {len(response_records)} form responses enties into RDS")

        except Exception as e:
            logger.exception = {
                f"Database error while inserting form responses. Error: {str(e)}"
            }
            raise e
