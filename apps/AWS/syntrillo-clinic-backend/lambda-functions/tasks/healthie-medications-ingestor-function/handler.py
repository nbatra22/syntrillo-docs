# Python standard library
from typing import Dict, Any
import json

# third party libraries (things you `pip install`)

# own/local libraries
from .utils import parse_and_transform_to_medication_record, update_medication_db

from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer
from syntrillo.bp_analysis.helpers import list_valid_active_healthie_patients
from syntrillo.api_healthie.medications import HealthieMedications


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function to retrieve and store all patients medications information.

    Args:
        event (dict): The event data passed to the Lambda function
        context (LambdaContext): Runtime information provided by AWS Lambda

    Returns:
        dict: Response object containing statusCode and body
    """
    logger.info({ "message": f"Event received: {json.dumps(event)}" })

    try:
        patient_information_list = list_valid_active_healthie_patients()
        patients = patient_information_list.get("users", {})
        healthie_medications = HealthieMedications()

        if not patients:
            logger.warning("No valid healthie patients available...")

        for patient in patients:
            syntrillo_internal_id = patient.get("syntrillo_internal_id")
            healthie_user_id = patient.get("healthie_user_id")

            # Get both the active and inactive medications
            response_active = healthie_medications.list_user_medications(healthie_user_id=healthie_user_id, active=True)
            response_inactive = healthie_medications.list_user_medications(healthie_user_id=healthie_user_id, active=True)

            data_active = response_active.get("medications", [])
            data_inactive = response_inactive.get("medications", [])

            for med_data in data_active:
                med_record = parse_and_transform_to_medication_record(med_data, syntrillo_internal_id)
                updated_at = med_data.get("updated_at")
                update_medication_db(med_record, updated_at)

            for med_data in data_inactive:
                med_record = parse_and_transform_to_medication_record(med_data, syntrillo_internal_id)
                updated_at = med_data.get("updated_at")
                update_medication_db(med_record, updated_at)



        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Data successfully ingested into RDS"
            }),
        }

    except Exception as e:
        logger.error({
            "message": f"Error in Healthie Data Ingestor Lambda execution: {str(e)}",
        })

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing data',
                'error': str(e)
            })
        }


if __name__ == "__main__":
    handler({}, None) # type: ignore
