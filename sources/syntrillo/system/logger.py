from aws_lambda_powertools import Logger
import os

def get_logger(service_name=None):
    if service_name is None:
        service_name = os.environ.get('SERVICE_NAME', 'default-service')

    log_level = os.environ.get('LOG_LEVEL', 'INFO')

    logger = Logger(
        service=service_name,
        level=log_level,
    )

    return logger

# Singleton instance
logger = get_logger()