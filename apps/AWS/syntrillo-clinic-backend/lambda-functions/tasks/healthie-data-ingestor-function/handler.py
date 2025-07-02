# Python standard library
from typing import Dict, Any
import json

# third party libraries (things you `pip install`)

# own/local libraries
from services.form_responses import FormResponseService
from services.form_templates import process_form_templates
from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer

@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Basic AWS Lambda handler function.

    Args:
        event (dict): The event data passed to the Lambda function
        context (LambdaContext): Runtime information provided by AWS Lambda

    Returns:
        dict: Response object containing statusCode and body
    """
    logger.info({
        "message": f"Event received: {json.dumps(event)}",
    })
    try:
        # Fetch form templates from Healthie and push data into Amazon RDS
        process_form_templates()

        # Process form responses and related medications
        form_service = FormResponseService()
        form_service.process()

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
    handler({}, None)
