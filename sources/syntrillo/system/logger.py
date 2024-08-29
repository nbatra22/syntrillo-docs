from aws_lambda_powertools import Logger
import os

def get_logger():    
    service_name = os.environ.get('SERVICE_NAME', 'default-service') # could be defined in cdk.context.json and passed to a lambda env var

    logger = Logger(
        service=service_name,
        # level=... # LOG_LEVEL is defined in the cdk.context.json for each environement and passed to POWERTOOLS_LOG_LEVEL lambda env variable
    )

    return logger

logger = get_logger()