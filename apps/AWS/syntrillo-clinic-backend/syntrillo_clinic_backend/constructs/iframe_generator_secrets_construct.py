from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3_notifications,
    aws_apigateway as apigw,
    aws_ssm as ssm,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_certificatemanager as acm,
    aws_efs as efs,
    aws_backup as backup,
    aws_efs as efs,
    aws_events as events,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
)
from constructs import Construct
import json

class IFrameGeneratorSecrets(Construct):
    def __init__(self, scope: Construct, id: str, environment_context: dict, database: Construct, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.environment_context = environment_context

        self.database = database

        custom_kms_key = kms.Key(
            self, "SecretsKmsKey",
            description="Custom KMS key for Secrets",
            enabled=True,
            enable_key_rotation=True,
            pending_window=Duration.days(30)
        )

        self.servers_stack_database_user_secrets = secretsmanager.Secret(
            self, "LambdaUserDatabaseSecrets",
            secret_name="LambdaUserDatabaseSecrets",
            encryption_key=custom_kms_key,
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({
                    "username": "syntrillo_clinic_lambda_user",
                    # "host": self.database.db_from_snapshot.instance_endpoint.hostname,
                }),
                generate_string_key="password",
                exclude_characters='/@"\\',
                # exclude_punctuation=True,
                include_space=False,
                password_length=32
            )
        )

        self.tenovi_hwi_secrets = secretsmanager.Secret(
            self, "TenoviHWISecrets",
            secret_name="TenoviHWISecrets",
            encryption_key=custom_kms_key
        )

        self.healthie_secrets = secretsmanager.Secret(
            self, "HealthieSecrets",
            secret_name="HealthieSecrets",
            encryption_key=custom_kms_key
        )

        self.openai_secrets = secretsmanager.Secret(
            self, "OpenAiSecrets",
            secret_name="OpenAiSecrets",
            encryption_key=custom_kms_key
        )

        