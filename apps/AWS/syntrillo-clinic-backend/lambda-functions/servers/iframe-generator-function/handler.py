from syntrillo.system.logger import logger
from syntrillo.system.tracer import tracer

import flask_app

# import awsgi
# @logger.inject_lambda_context(log_event=True)
# def handler(event, context):
#     base64_content_types = ['image/vnd.microsoft.icon', 'image/x-icon']
#     return awsgi.response(flask_app.app, event, context, base64_content_types) 

from apig_wsgi import make_lambda_handler

@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def handler(event, context):
    return make_lambda_handler(flask_app.app, binary_support=True)(event, context)