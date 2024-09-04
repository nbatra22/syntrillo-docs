import flask_app

from apig_wsgi import make_lambda_handler

from aws_lambda_powertools import Logger
logger = Logger()

@logger.inject_lambda_context(log_event=True)
def simple_handler(event, context):
    return make_lambda_handler(flask_app.app, binary_support=True)(event, context)