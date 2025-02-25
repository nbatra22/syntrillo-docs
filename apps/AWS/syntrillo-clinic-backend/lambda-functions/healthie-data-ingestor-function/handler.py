# Python standard library
from typing import Dict, Any
import json
import logging

# third party libraries (things you `pip install`)

# own/local libraries
from form_responses import ( process_form_responses )
from form_templates import ( process_form_templates )

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Basic AWS Lambda handler function.

    Args:
        event (dict): The event data passed to the Lambda function
        context (LambdaContext): Runtime information provided by AWS Lambda

    Returns:
        dict: Response object containing statusCode and body
    """
    # TODO: use lambda power tools library for logging instead of logger
    logger.info("Event received: %s", json.dumps(event))
    try:
        # Fetch form templates from Healthie and push data into Amazon RDS
        process_form_templates()
        # Fetch form responses from Healthie and push data into Amazon RDS
        process_form_responses()

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Data successfully ingested into RDS"
            }),
        }

    except Exception as e:
        logger.info(f"Error in Lambda execution: {str(e)}")

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing data',
                'error': str(e)
            })
        }


if __name__ == "__main__":
    handler( {}, None)
