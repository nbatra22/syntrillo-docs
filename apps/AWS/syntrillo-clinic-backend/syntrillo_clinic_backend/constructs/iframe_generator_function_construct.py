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
    aws_iam as iam,
)
from constructs import Construct

class IFrameGeneratorFunction(Construct):
    def __init__(self, scope: Construct, id: str,
                 environment_context: dict,
                 network: Construct, 
                 database: Construct,
                 storage: Construct,
                 secrets: Construct,
                 llm_server: Construct,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        self.environment_context = environment_context
        self.network = network
        self.database = database
        self.storage = storage
        self.secrets = secrets
        self.llm_server = llm_server

        params_and_secrets = _lambda.ParamsAndSecretsLayerVersion.from_version(_lambda.ParamsAndSecretsVersions.V1_0_103,
            cache_size=500,
            log_level=_lambda.ParamsAndSecretsLogLevel.NONE
        )

        self.function = _lambda.Function(self, "IFrameGeneratorFunction",
            function_name="IFrameGeneratorFunction",
            vpc = self.network.vpc,
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda-functions/iframe-generator-function", exclude=['.env']),
            params_and_secrets=params_and_secrets,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.storage.efs_access_point,
                "/mnt/python_modules"
            ),
            environment={
                "POWERTOOLS_LOG_LEVEL": self.environment_context['iframe_generator_function']['log_level'],
                "PYTHONPATH": "/mnt/python_modules",
                "AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN": self.secrets.database_lambda_user_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN": self.secrets.tenovi_hwi_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN": self.secrets.healthie_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN": self.secrets.openai_secrets.secret_arn
            },
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=self.environment_context['iframe_generator_function']['memory_size'], 
            timeout=Duration.seconds(self.environment_context['iframe_generator_function']['lambda_time_out_seconds']),
            reserved_concurrent_executions=self.environment_context['iframe_generator_function']['reserved_concurrent_executions']
        )

        self.function_alias = _lambda.Alias(
            self, "LambdaAlias",
            alias_name="provisionned-concurrency",
            version=self.function.current_version,
            provisioned_concurrent_executions=self.environment_context['iframe_generator_function']['provisioned_concurrency_executions']
        )

        # self.database.admin_secret.grant_read(self.function)
        self.grant_read_secrets(self.secrets.database_lambda_user_secrets)
        # self.secrets.tenovi_hwi_secrets.grant_read(self.function)
        self.grant_read_secrets(self.secrets.tenovi_hwi_secrets)
        # self.secrets.healthie_secrets.grant_read(self.function)
        self.grant_read_secrets(self.secrets.healthie_secrets)
        # self.secrets.openai_secrets.grant_read(self.function)
        self.grant_read_secrets(self.secrets.openai_secrets)

        function_security_group = self.function.connections.security_groups[0]

        self.database.db_from_snapshot_security_group.add_ingress_rule(
            function_security_group,
            ec2.Port.tcp(3306),
            description=f"Allow inbound traffic from IFrameGeneratorFunction on port 3306"
        )

        self.database.db_from_snapshot_security_group.add_ingress_rule(
            function_security_group,
            ec2.Port.tcp(3306),
            description=f"Allow inbound traffic from IFrameGeneratorFunction on port 3306"
        )

        self.llm_server.security_group.add_ingress_rule(
            function_security_group,
            ec2.Port.tcp(443),
            "Allow LLM server access httpS"
        )

        self.llm_server.security_group.add_ingress_rule(
            function_security_group,
            ec2.Port.tcp(80),
            "Allow LLM server access http"
        ) 
    
    def grant_read_secrets(self, secrets):
        # Must be used instead of grant_read to avoid circular dependency (n.b.: No real explanation why it creates a circular dependency)
        self.function.add_to_role_policy(iam.PolicyStatement(
            actions=["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue"],
            resources=[secrets.secret_arn],
        ))
        self.function.add_to_role_policy(iam.PolicyStatement(
            actions=["kms:Decrypt"],
            resources=[secrets.encryption_key.key_arn],
        ))
