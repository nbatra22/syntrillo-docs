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

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class SecretsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context

        self.termination_protection = self.environment_context["stacks-termination-protection"]

        custom_kms_key = kms.Key(
            self, "SecretsKmsKey",
            description="Custom KMS key for Secrets",
            enabled=True,
            enable_key_rotation=True,
            pending_window=Duration.days(30)
        )

        self.tenovi_hwi_secrets = secretsmanager.Secret(
            self, "TenoviHWISecrets",
            encryption_key=custom_kms_key
        )

        self.healthie_secrets = secretsmanager.Secret(
            self, "HealthieSecrets",
            encryption_key=custom_kms_key
        )

        self.openai_secrets = secretsmanager.Secret(
            self, "OpenAiSecrets",
            encryption_key=custom_kms_key
        )