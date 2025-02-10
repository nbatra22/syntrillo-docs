from typing import Dict, Any
import json
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Basic AWS Lambda handler function.
    
    Args:
        event (dict): The event data passed to the Lambda function
        context (LambdaContext): Runtime information provided by AWS Lambda
    
    Returns:
        dict: Response object containing statusCode and body
    """
    logger.info("Event received: %s", json.dumps(event))

    # Get list of all forms
    # Healthie API calls

    # For each form collect all the questions and answers

    # Push data to MySQL database


    
    try:
        # Extract data from the event (if it's an API Gateway event)
        if 'body' in event:
            body = json.loads(event.get('body', '{}'))
        else:
            body = event
            
        # Process the request
        message = body.get('message', 'Hello from Lambda!')
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare the response
        response_body = {
            'message': message,
            'timestamp': timestamp,
            'requestId': context.aws_request_id
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # For CORS support
            },
            'body': json.dumps(response_body)
        }

    except Exception as e:
        logger.error("Error processing request: %s", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }

if __name__ == "__main__":
    main()
