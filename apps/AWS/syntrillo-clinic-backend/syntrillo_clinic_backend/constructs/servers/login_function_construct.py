from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Fn,
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
    aws_iam as iam,
)
from constructs import Construct

import time

class LoginFunction(Construct):
    def __init__(self, scope: Construct, id: str,
                 environment_context: dict,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        self.environment_context = environment_context

        # ---------------------------------------------------------------------
        # INPUTS
        # ---------------------------------------------------------------------

        # Cognito User Pool Client Id
        self.user_pool_client_id = Fn.import_value("SyntrilloClinic-Authentication-UserPoolClient-Id")

        # ---------------------------------------------------------------------      

        self.function = _lambda.Function(self, "LoginFunction",
            function_name="LoginFunction",
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda-functions/login-function", exclude=['.env', '__pycache__']),
            environment={
                "CLIENT_ID": self.user_pool_client_id,
            },
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=self.environment_context['login_function']['memory_size'], 
            timeout=Duration.seconds(self.environment_context['login_function']['lambda_time_out_seconds']),
            reserved_concurrent_executions=self.environment_context['login_function']['reserved_concurrent_executions'],
            description=f"Generated at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        self.function_alias = _lambda.Alias(
            self, "LambdaAlias",
            alias_name="provisionned-concurrency",
            version=self.function.current_version,
            provisioned_concurrent_executions=self.environment_context['iframe_generator_function']['provisioned_concurrency_executions']
        )


        # ---------------------------------------------------------------------
        # EXPORT VALUES
        # ---------------------------------------------------------------------

        # -
