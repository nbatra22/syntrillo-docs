import os
from syntrillo.system.logger import logger

def get_aws_environment() -> str:
    """
    Get the environment from the SSM parameter store
    Args:
        None
    Returns:
        str: The AWS environment
    Raises:
        e (Exception): General exception from retrieving the AWS environment variable
    """
    # Initialize AWS Systems Manager (SSM) client
    logger.info("Retrieving environment variable from AWS...")
    try:
        AWS_ENVIRONMENT = os.environ['AWS_ENVIRONMENT']
        logger.info(f"Successfully retrieved AWS env. Environment: {AWS_ENVIRONMENT}")
        return AWS_ENVIRONMENT

    except Exception as e:
        logger.error(f"Error retrieving environment variable from AWS: {e}")
        raise e