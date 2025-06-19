from syntrillo.billing.billing_manager import BillingManager
from syntrillo.billing.candid_manager import CandidHealthManager
from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer
from syntrillo.aws_helpers.env_utils import get_aws_environment

@tracer.capture_lambda_handler # TODO: comment out decorator when running locally
@logger.inject_lambda_context(log_event=True) # TODO: comment out decorator when running locally
def handler(event, context):
    try:
        # Sync Candid Billing Data
        candid_manager = CandidHealthManager()
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
