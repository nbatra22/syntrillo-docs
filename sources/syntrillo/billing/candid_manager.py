from candid.client import CandidApiClient
from syntrillo.billing.models import Claim
from syntrillo.pseudonyms_management.lookup_codes_management import LookUpCodesManagement
from syntrillo.remote_monitoring.syntrillo_database_manager import SyntrilloDatabaseManager
from syntrillo.system.logger import logger
from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets
from syntrillo.billing.constants import CPT_CODE


class CandidApiClientEnvironment:
    """
    Candid Health's Environment class which was copy and pasted from their library
    Library URL: https://github.com/candidhealth/candid-python/blob/master/src/candid/environment.py
    """
    def __init__(self, *, candid_api: str, pre_encounter: str):
        self.candid_api = candid_api
        self.pre_encounter = pre_encounter


class CandidHealthManager:
    """
    This class is used to manage the candid health of the patients
    """
    def __init__(self, response_limit: int = 100):

        # Load Candid Credentials
        secrets = LocalEnvironmentAndSecrets(load_candid_secrets=True)

        logger.info(f"is local: {secrets.is_local()}; is staging: {secrets.is_staging()}; is production: {secrets.is_production()}; is lambda: {secrets.is_lambda()}; is pythonanywhere: {secrets.is_pythonanywhere()}")

        # Retrieve necessary secerts from AWS Secrets Manger
        client_id = secrets.get_secret_value('candid', 'client_id')
        client_secret = secrets.get_secret_value('candid', 'client_secret')
        candid_api = secrets.get_secret_value('candid', 'candid_api')
        pre_encounter = secrets.get_secret_value('candid', 'pre_encounter')

        # Set required environment variable for the Candid client
        environment = CandidApiClientEnvironment(candid_api=candid_api, pre_encounter=pre_encounter)

        # # Set up the candid client to make api calls (without having to retrieve new credential tokens every _ minutes)
        self.client = CandidApiClient(environment=environment, client_id=client_id, client_secret=client_secret)

        self.db_manager = SyntrilloDatabaseManager(syntrillo_internal_key="NOT_USED")
        self.lookup_codes_manager = LookUpCodesManagement()
        self.response_limit = response_limit
        self.cpt_bp_code = CPT_CODE


    def sync_candid_billing_data(self):
        """
        1. Retrieves all the billing info from Candid's apis
        2. Takes the billing info and inserts/updates Syntrillo's AWS RDS table "billing_records"

        Args:
            None
        Returns:
            None
        """

        try:
            all_enounter_data = self.retrieve_all_patients_billing_info()
            self.insert_claims_to_sql(all_enounter_data)

        except Exception as e:
            logger.error(f"Failed to sync candid billing data: {e}")
            raise e


    def retrieve_all_patients_billing_info(self) -> list[Claim]:
        """
        API: https://docs.joincandidhealth.com/api-reference/encounters/v-4/get-all
        Gets all patients billing data

        Args:
            None
        Returns:
            all_claims_data (list[Claim]): List of all claims
        Raises:
            Exception: any type of exception while getting candid data
        """
        page_token = ""
        all_claims_data = []
        try:
            healthie_id_to_syntrillo_internal_key_mapping = self.lookup_codes_manager.retrieve_healthie_id_to_syntrillo_internal_key_mapping()
            while True:
                encounters = self.client.encounters.v_4.get_all(
                    limit=self.response_limit,
                    page_token=page_token
                )

                items = encounters.items # basically the encounters which have the claims nested in them

                # Retreive next page token for pagenation (thinking about when we will have millions of billing records in Candid)
                page_token = encounters.next_page_token

                for item in items:
                    encounter_id = item.encounter_id
                    healthie_id = item.patient.external_id

                    syntrillo_internal_key = healthie_id_to_syntrillo_internal_key_mapping.get(healthie_id)
                    if not syntrillo_internal_key:
                        logger.error(f"No syntrillo_internal_key found for tenovi_patient_id: {healthie_id}")
                        raise Exception(f"No syntrillo_internal_key found for tenovi_patient_id: {healthie_id}")

                    for claim in item.claims:
                        claim_status = claim.status

                        for service in claim.service_lines:
                            cpt_code = service.procedure_code
                            service_line_id = service.service_line_id
                            claim_id = service.claim_id
                            date_of_service_start = service.date_of_service_range.start_date
                            date_of_service_end = service.date_of_service_range.end_date

                            single_claim_data = Claim(
                                service_line_id=str(service_line_id),
                                claim_id=str(claim_id),
                                encounter_id=str(encounter_id),
                                claim_status=claim_status,
                                syntrillo_internal_key=str(syntrillo_internal_key),
                                cpt_code=str(cpt_code),
                                date_of_service_start=str(date_of_service_start),
                                date_of_service_end=str(date_of_service_end),
                            )
                            all_claims_data.append(single_claim_data)

                if not page_token:
                    break

        except Exception as e:
            logger.exception("Error while pinging Candid API and converting data to Claim objects.")
            raise e

        return all_claims_data


    def insert_claims_to_sql(self, all_enounter_data: list[Claim]) -> None:
        """
        Saves the given list of Claim to Amazon RDS

        Args:
            all_enounter_data (list[Claim]): the list of Claim to be saved
        Returns:
            None: the function does not return anything
        Raises:
            Exception: any type of exception while saving the data
        """

        if not all_enounter_data:
            logger.warning("No claims to insert into database")
            return None
        logger.info(f"Inserting {len(all_enounter_data)} claims into database")

        db_connection = self.db_manager.conn

        try:
            with db_connection.cursor() as cursor:
                sql_query = """
                    INSERT INTO billing_records (
                        service_line_id,
                        claim_id,
                        encounter_id,
                        claim_status,
                        syntrillo_internal_key,
                        cpt_code,
                        date_of_service_start,
                        date_of_service_end
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        claim_id=VALUES(claim_id),
                        encounter_id=VALUES(encounter_id),
                        claim_status=VALUES(claim_status),
                        syntrillo_internal_key=VALUES(syntrillo_internal_key),
                        cpt_code=VALUES(cpt_code),
                        date_of_service_start=VALUES(date_of_service_start),
                        date_of_service_end=VALUES(date_of_service_end);
                """

                # Convert to list of tuples for executemany function requirement
                claim_records = [
                    (
                        claim.service_line_id,
                        claim.claim_id,
                        claim.encounter_id,
                        claim.claim_status,
                        claim.syntrillo_internal_key,
                        claim.cpt_code,
                        claim.date_of_service_start,
                        claim.date_of_service_end
                    )
                    for claim in all_enounter_data
                ]

                # Execute a bulk query with tuples
                cursor.executemany(sql_query, claim_records)
                db_connection.commit()

                logger.info(f"Successfully inserted or updated {len(claim_records)} billing enties into RDS")

        except Exception as e:
            logger.exception = {
                f"Database error while inserting Billing entries. Error: {str(e)}"
            }
            raise e


    def get_patient_billing_data(self, syntrillo_internal_key: str) -> list[dict]:
        """
        Retrieves single patient's billing data from AWS RDS billing_records table

        Args:
            syntrillo_internal_key (str): syntrillo internal key
        Returns:
            billing_records (list[dict]): list of billing records
        Raises:
            Exception: any type of exception while getting the billing data
        """
        if not syntrillo_internal_key:
            logger.warning("No syntrillo internal key provided...")
            return None

        db_connection = self.db_manager.conn
        logger.info(f"Getting billing data for patient with syntrillo_internal_key {syntrillo_internal_key}")
        try:
            with db_connection.cursor() as cursor:
                sql_query = """
                    SELECT claim_status, date_of_service_start
                    FROM billing_records br
                        WHERE br.syntrillo_internal_key = %s
                            AND br.cpt_code = %s
                """
                cursor.execute(sql_query, (syntrillo_internal_key, self.cpt_bp_code))
                results = cursor.fetchall()

                billing_records = []
                for res in results:
                    billing_records.append({
                        "status": res[0],
                        "date_of_service": res[1]
                    })
                logger.info(f"Billing data for patient with syntrillo_internal_key {syntrillo_internal_key} retrieved successfully")
                return billing_records

        except Exception as e:
            logger.exception = {
                f"Database error while getting Billing entry for a single patient."
            }
            raise e

if __name__ == "__main__":
    candid_manager = CandidHealthManager()
    print(candid_manager.get_patient_bp_billing_data(5311453))
