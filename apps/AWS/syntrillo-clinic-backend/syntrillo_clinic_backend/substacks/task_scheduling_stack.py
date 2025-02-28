from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
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
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
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

        # -----------------------------------------------------------------------
        # Remote monitoring Lambdas

        self.remote_monitoring_data_sync_function = _lambda.Function(self, "RemoteMonitoringDataSyncFunction",
            function_name="RemoteMonitoringDataSyncFunction",
            vpc = self.network.vpc,
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda-functions/remote-monitoring-data-sync-function", exclude=['.env', '__pycache__']),
            params_and_secrets=params_and_secrets,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.storage.efs_access_point,
                "/mnt/python_modules"
            ),
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "PYTHONPATH": "/mnt/python_modules",
                "AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN": self.secrets.database_lambda_user_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN": self.secrets.tenovi_hwi_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN": self.secrets.healthie_secrets.secret_arn
            },
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=512,
            timeout=Duration.seconds(600),
        )

        self.grant_read_secrets(self.remote_monitoring_data_sync_function, self.secrets.database_lambda_user_secrets)
        self.grant_read_secrets(self.remote_monitoring_data_sync_function, self.secrets.tenovi_hwi_secrets)
        self.grant_read_secrets(self.remote_monitoring_data_sync_function, self.secrets.healthie_secrets)

        function_security_group = self.remote_monitoring_data_sync_function.connections.security_groups[0]

        self.database.db_from_snapshot_security_group.add_ingress_rule(
            function_security_group,
            ec2.Port.tcp(3306),
            description=f"Allow inbound traffic from RemoteMonitoringDataSyncFunction on port 3306"
        )

    def grant_read_secrets(self, function, secrets):
        # Must be used instead of grant_read to avoid circular dependency (n.b.: No real explanation why it creates a circular dependency)
        function.add_to_role_policy(iam.PolicyStatement(
            actions=["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue"],
            resources=[secrets.secret_arn],
        ))
        function.add_to_role_policy(iam.PolicyStatement(
            actions=["kms:Decrypt"],
            resources=[secrets.encryption_key.key_arn],
        ))


class HealthieDataIngestor(Construct):
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

        # -----------------------------------------------------------------------
        # Remote monitoring Lambdas

        self.healthie_data_ingestor_function = _lambda.Function(self, "HealthieDataIngestorFunction",
            function_name="HealthieDataIngestorFunction",
            vpc = self.network.vpc,
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda-functions/healthie-data-ingestor-function", exclude=['.env', '__pycache__']),
            params_and_secrets=params_and_secrets,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.storage.efs_access_point,
                "/mnt/python_modules"
            ),
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "PYTHONPATH": "/mnt/python_modules",
                "AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN": self.secrets.database_lambda_user_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN": self.secrets.tenovi_hwi_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN": self.secrets.healthie_secrets.secret_arn
            },
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=512,
            timeout=Duration.seconds(600),
        )

        self.grant_read_secrets(self.healthie_data_ingestor_function, self.secrets.database_lambda_user_secrets)
        self.grant_read_secrets(self.healthie_data_ingestor_function, self.secrets.tenovi_hwi_secrets)
        self.grant_read_secrets(self.healthie_data_ingestor_function, self.secrets.healthie_secrets)

        function_security_group = self.healthie_data_ingestor_function.connections.security_groups[0]

        self.database.db_from_snapshot_security_group.add_ingress_rule(
            function_security_group,
            ec2.Port.tcp(3306),
            description=f"Allow inbound traffic from RemoteMonitoringDataSyncFunction on port 3306"
        )

    def grant_read_secrets(self, function, secrets):
        # Must be used instead of grant_read to avoid circular dependency (n.b.: No real explanation why it creates a circular dependency)
        function.add_to_role_policy(iam.PolicyStatement(
            actions=["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue"],
            resources=[secrets.secret_arn],
        ))
        function.add_to_role_policy(iam.PolicyStatement(
            actions=["kms:Decrypt"],
            resources=[secrets.encryption_key.key_arn],
        ))

class DataSyncWorkflow(Construct):
    def __init__(self, scope: Construct, id: str,
                 remote_monitoring_data_sync_function: _lambda.Function,
                 pii_data_sync_function: _lambda.Function,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create Step Functions tasks
        list_patients_task = tasks.LambdaInvoke(
            self, "ListPatients",
            lambda_function=remote_monitoring_data_sync_function,
            payload=sfn.TaskInput.from_object({
                "action": "list_patients"
            }),
            result_path="$",
            result_selector={
                "users.$": "$.Payload.users",
            }
        )

        sync_patient_task = tasks.LambdaInvoke(
            self, "SyncPatientData",
            lambda_function=remote_monitoring_data_sync_function,
            payload=sfn.TaskInput.from_object({
                "action": "sync_patient",
                "id.$": "$.id"
            }),
            result_path="$",
            result_selector={
                "success.$": "$.Payload.success",
                "error.$": "$.Payload.error"
            }
        )

        # Create Map state for processing patients
        map_state = sfn.Map(
            self, "ProcessEachPatient",
            max_concurrency=5,
            items_path="$.users"
        )

        map_state.item_processor(sync_patient_task)

        # Add PII sync task
        pii_sync_task = tasks.LambdaInvoke(
            self, "PIISyncTask",
            lambda_function=pii_data_sync_function,
            payload=sfn.TaskInput.from_object({
                "action": "sync_pii"
            }),
            result_path="$"
        )

        # Create the state machine
        self.state_machine = sfn.StateMachine(
            self, "StepFunctionsDataSyncWorkflow",
            state_machine_name="StepFunctionsDataSyncWorkflow",
            definition_body=sfn.DefinitionBody.from_chainable(
                list_patients_task.next(map_state.next(pii_sync_task))
            ),
            timeout=Duration.minutes(30),
            tracing_enabled=True
        )

        # Create a scheduled event rule
        # we prefer a cron expression instead of a rate, because with a rate we do not know exactly when
        # the lambda is triggered. With cron, you can decide exactly when you start.
        # This avoids using database resources during working hours
        schedule = events.Schedule.cron(
            minute="0",
            hour="0/6",
            month="*",
            week_day="*",
            year="*",
        )

        event_rule = events.Rule(
            self, "RemoteMonitoringDataSyncRule",
            schedule=schedule,
            enabled=True,
        )

        # Add the state machine as a target for the rule
        event_rule.add_target(
            targets.SfnStateMachine(self.state_machine)
        )
        
class PIIDataSync(Construct):
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

        self.aws_environment = aws_environment

        params_and_secrets = _lambda.ParamsAndSecretsLayerVersion.from_version(_lambda.ParamsAndSecretsVersions.V1_0_103,
            cache_size=500,
            log_level=_lambda.ParamsAndSecretsLogLevel.DEBUG
        )

        # -----------------------------------------------------------------------
        # Pii Sync Lambdas

        self.pii_data_sync_function = _lambda.Function(self, "PIIDataSyncFunction",
            function_name="PIIDataSyncFunction",
            vpc = self.network.vpc,
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda-functions/pii-data-sync-function", exclude=['.env', '__pycache__']),
            params_and_secrets=params_and_secrets,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.storage.efs_access_point,
                "/mnt/python_modules"
            ),
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "PYTHONPATH": "/mnt/python_modules",
                "AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN": self.secrets.database_lambda_user_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN": self.secrets.tenovi_hwi_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN": self.secrets.healthie_secrets.secret_arn,
                "PII_DATA_BUCKET": f"{self.aws_environment}.syntrillo-analytics.pii-data"
            },
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=512,
            timeout=Duration.seconds(600),
        )

        self.grant_read_secrets(self.pii_data_sync_function, self.secrets.database_lambda_user_secrets)
        self.grant_read_secrets(self.pii_data_sync_function, self.secrets.tenovi_hwi_secrets)
        self.grant_read_secrets(self.pii_data_sync_function, self.secrets.healthie_secrets)

        self.function_security_group = self.pii_data_sync_function.connections.security_groups[0]

        # ---------------------------------------------------------------------
        # EXPORT VALUES
        # ---------------------------------------------------------------------

        CfnOutput(self, "PIIDataSyncFunctionSecurityGroup",
            value=self.function_security_group.security_group_id,
            export_name="PIIDataSyncFunctionSecurityGroup"
        )

        CfnOutput(self, "PIIDataSyncFunctionRoleArn",
            value=self.pii_data_sync_function.role.role_arn,
            export_name="PIIDataSyncFunctionRoleArn"
        )

    def grant_read_secrets(self, function, secrets):
        # Must be used instead of grant_read to avoid circular dependency (n.b.: No real explanation why it creates a circular dependency)
        function.add_to_role_policy(iam.PolicyStatement(
            actions=["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue"],
            resources=[secrets.secret_arn],
        ))
        function.add_to_role_policy(iam.PolicyStatement(
            actions=["kms:Decrypt"],
            resources=[secrets.encryption_key.key_arn],
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

        pii_data_sync = PIIDataSync(
            self, "PIIDataSyncFunction",
            aws_environment=self.aws_environment,
            network=self.network,
            database=self.database,
            storage=self.storage,
            secrets=self.secrets,
        )

        data_sync_workflow = DataSyncWorkflow(
            self, "DataSyncFunction",
            remote_monitoring_data_sync_function = remote_monitoring_data_sync.remote_monitoring_data_sync_function,
            pii_data_sync_function = pii_data_sync.pii_data_sync_function,
        )

        healthie_data_ingestor = HealthieDataIngestor(
            self, "HealthieDataIngestor",
            aws_environment=self.aws_environment,
            network=self.network,
            database=self.database,
            storage=self.storage,
            secrets=self.secrets,
        )
