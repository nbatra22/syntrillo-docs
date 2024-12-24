import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info(f"Received event: {event}")
    logger.info(f"Context: {context}")
    return {
        'statusCode': 200,
        'body': 'Hello, World!'
    }