from syntrillo.billing.billing_manager import BillingManager
from syntrillo.billing.candid_manager import CandidHealthManager
from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer
from syntrillo.aws_helpers.env_utils import get_aws_environment

# TODO: comment these decorators when running locally 
@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    try:
        # General set up and retrieval of environment and secrets
        env = get_aws_environment()
        if not env:
            logger.error("Environment variablenot found ...")
            return

        # Sync Candid Billing Data
        candid_manager = CandidHealthManager(env)
        candid_manager.sync_candid_billing_data()

        # Sync Billing Eligibility Data
        billing_manager = BillingManager()
        billing_manager.sync_billing_eligibility_data()

        return {
            'statusCode': 200,
            'body': 'Successfully synced Candid Billing Ingestor event'
        }

    except Exception as e:
        logger.exception(f"An error occurred in the Candid Billing Ingestor: {e}")
        return {
            'statusCode': 500,
            'body': 'Error in Candid Billing Ingestor lambda function.'
        }

