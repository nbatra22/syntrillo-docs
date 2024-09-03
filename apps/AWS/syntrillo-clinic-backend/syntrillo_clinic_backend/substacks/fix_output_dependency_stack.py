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
)
from constructs import Construct

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class FixOutputDependencyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, secrets: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.secrets = secrets

        # ssm.StringParameter(
        #     self, "TemporaryFixOutputDependencyParameter",
        #     parameter_name="/tmp/fix_output_dependency",
        #     string_value=self.secrets.tenovi_hwi_secrets.secret_arn,
        # )