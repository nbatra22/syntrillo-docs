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
    aws_events_targets as targets,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
)
from constructs import Construct

# -----------------------------------------------------------------------------
# CONSTRUCTS
# -----------------------------------------------------------------------------
class RemoteMonitoringDataSync(Construct):
    def __init__(self, scope: Construct, id: str, 
                 aws_environment: str, 
                 network: Construct, 
                 database: Construct,
                 storage: Construct,
                 secrets: Construct,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        self.network = network
        self.database = database
        self.storage = storage
        self.secrets = secrets

        params_and_secrets = _lambda.ParamsAndSecretsLayerVersion.from_version(_lambda.ParamsAndSecretsVersions.V1_0_103,
            cache_size=500,
            log_level=_lambda.ParamsAndSecretsLogLevel.DEBUG
        )

        self.remote_monitoring_data_sync_function = _lambda.Function(self, "RemoteMonitoringDataSyncFunction",
            function_name="RemoteMonitoringDataSyncFunction",
            vpc = self.network.vpc,
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda-functions/remote-monitoring-data-sync-function", exclude=['.env']),
            params_and_secrets=params_and_secrets,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.storage.efs_access_point,
                "/mnt/python_modules"
            ),
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "PYTHONPATH": "/mnt/python_modules",
                "AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN": self.database.admin_secret.secret_arn,
                "AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN": self.secrets.tenovi_hwi_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN": self.secrets.healthie_secrets.secret_arn
            },
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=512,
            timeout=Duration.seconds(600),
        )

        # self.database.admin_secret.grant_read(self.function)
        self.grant_read_secrets(self.database.admin_secret)
        # self.secrets.tenovi_hwi_secrets.grant_read(self.function)
        self.grant_read_secrets(self.secrets.tenovi_hwi_secrets)
        # self.secrets.healthie_secrets.grant_read(self.function)
        self.grant_read_secrets(self.secrets.healthie_secrets)

        # Create a scheduled event rule
        # we prefer a cron expression instead of a rate, because with a rate we do not know exactly when
        # the lambda is triggered. With cron, you can decide exactly when you start.
        # This avoids using database resources during working hours
        schedule = events.Schedule.cron(
            minute="0",
            hour="0",
            month="*",
            week_day="*",
            year="*",
        )

        event_rule = events.Rule(
            self, "RemoteMonitoringDataSyncRule",
            schedule=schedule,
            enabled=True,
        )

        # Add the Lambda function as a target for the scheduled event
        event_rule.add_target(
            targets.LambdaFunction(
                self.remote_monitoring_data_sync_function,
            )
        )

    def grant_read_secrets(self, secrets):
        # Must be used instead of grant_read to avoid circular dependency (n.b.: No real explanation why it creates a circular dependency)
        self.remote_monitoring_data_sync_function.add_to_role_policy(iam.PolicyStatement(
            actions=["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue"],
            resources=[secrets.secret_arn],
        ))

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class SyntrilloClinicTaskSchedulingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, 
                 environment_context: dict,
                 network: Construct, 
                 database: Construct,
                 storage: Construct,
                 secrets: Construct,
                 lambda_function: _lambda.Function, 
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.aws_environment = environment_context["environment_name"]
        self.network = network
        self.database = database
        self.storage = storage
        self.secrets = secrets

        self.termination_protection = self.environment_context["stacks-termination-protection"]

        remote_monitoring_data_sync = RemoteMonitoringDataSync(
            self, "RemoteMonitoringDataSyncFunction",
            aws_environment=self.aws_environment,
            network=self.network,
            database=self.database,
            storage=self.storage,
            secrets=self.secrets,
        )