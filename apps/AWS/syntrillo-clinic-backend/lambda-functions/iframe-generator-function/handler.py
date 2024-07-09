import awsgi

from aws_lambda_powertools import Logger
logger = Logger(service="IFRAME_GENERATOR")

import flask_app

@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    logger.info(f"[IFRAME GENERATOR FUNCTION] <STARTED>")
    return awsgi.response(flask_app.app, event, context)