from aws_lambda_powertools import Tracer
import os

def get_tracer():
    service_name = os.environ.get('SERVICE_NAME', 'default-service') # could be defined in cdk.context.json and passed to a lambda env var

    tracer = Tracer(service=service_name)

    return tracer

tracer = get_tracer()