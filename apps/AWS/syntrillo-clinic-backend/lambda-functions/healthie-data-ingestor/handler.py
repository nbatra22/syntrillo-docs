# Python standard library
from typing import Dict, Any
import json

# third party libraries (things you `pip install`)

# own/local libraries
from form_responses import ( process_form_responses )
from form_templates import ( process_form_templates )
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
    # TODO: use lambda power tools library for logging instead of logger
    logger.info({
        "message": f"Event received: {json.dumps(event)}",
        "correlation_id": context.get("aws_request_id", "unknown"),
    })
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
        logger.error({
            "message": f"Error in Healthie Data Ingestor Lambda execution: {str(e)}",
            "correlation_id": context.get("aws_request_id", "unknown"),
        })

        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing data',
                'error': str(e)
            })
        }


if __name__ == "__main__":
    handler( {}, None)
