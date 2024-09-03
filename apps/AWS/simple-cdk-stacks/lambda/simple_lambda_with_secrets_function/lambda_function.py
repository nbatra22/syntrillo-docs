# create a lambda function handler that returns hello
import os
import boto3
secrets_manager = boto3.client('secretsmanager')

def simple_handler(event, context):
    # read environment variable
    secret_arn = os.environ.get('SECRET_1')

    print(f"Secret ARN: {secret_arn}")

    # read secrets in secrets manager
    secret_value = secrets_manager.get_secret_value(SecretId=secret_arn)

    print(secret_value)

    return {
        'statusCode': 200,
        'body': secret_value['Name']
    }

