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

class MessageEndpointFunction(Construct):
    def __init__(self, scope: Construct, id: str,
                 environment_context: dict,
                 network: Construct, 
                 database: Construct,
                 storage: Construct,
                 secrets: Construct,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        self.environment_context = environment_context
        self.network = network
        self.database = database
        self.storage = storage
        self.secrets = secrets

        params_and_secrets = _lambda.ParamsAndSecretsLayerVersion.from_version(_lambda.ParamsAndSecretsVersions.V1_0_103,
            cache_size=500,
            log_level=_lambda.ParamsAndSecretsLogLevel.NONE
        )

        # Import file system endpoint
        efs_file_system_id = Fn.import_value("SyntrilloClinicEFSFileStystemId")
        imported_file_system = efs.FileSystem.from_file_system_attributes(
            self,
            "ImportedFileSystem",
            file_system_id=efs_file_system_id,
            security_group=storage.efs_security_group
        )

        efs_access_point_chatbots_arn = Fn.import_value("EFSAccessPointChatbotsArn")
        efs_access_point_chatbots = efs.AccessPoint.from_access_point_attributes(
            self,
            "EFSAccessPointChatbots",
            access_point_arn=efs_access_point_chatbots_arn,
            file_system=imported_file_system
        )

        # Create function
        self.function = _lambda.Function(self, "MessageEndpointFunction",
            function_name="MessageEndpointFunction",
            vpc = self.network.vpc,
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("lambda-functions/iframe-generator-function", exclude=['.env']),
            params_and_secrets=params_and_secrets,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                efs_access_point_chatbots,
                mount_path="/mnt/chatbots-resources"
            ),
            environment={
                "POWERTOOLS_LOG_LEVEL": self.environment_context['message_endpoint_function']['log_level'],
                "PYTHONPATH": "/mnt/chatbots-resources/python_modules",
                "AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN": self.secrets.database_lambda_user_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN": self.secrets.tenovi_hwi_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN": self.secrets.healthie_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN": self.secrets.openai_secrets.secret_arn
            },
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=self.environment_context['message_endpoint_function']['memory_size'], 
            timeout=Duration.seconds(self.environment_context['message_endpoint_function']['lambda_time_out_seconds']),
            reserved_concurrent_executions=self.environment_context['message_endpoint_function']['reserved_concurrent_executions']
        )

        self.function_alias = _lambda.Alias(
            self, "LambdaAlias",
            alias_name="provisionned-concurrency",
            version=self.function.current_version,
            provisioned_concurrent_executions=self.environment_context['message_endpoint_function']['provisioned_concurrency_executions']
        )

        self.grant_read_secrets(self.secrets.database_lambda_user_secrets)
        self.grant_read_secrets(self.secrets.tenovi_hwi_secrets)
        self.grant_read_secrets(self.secrets.healthie_secrets)
        self.grant_read_secrets(self.secrets.openai_secrets)

        self.function_security_group = self.function.connections.security_groups[0]

        # !!! DO NOT USE THE EXAMPLE BELOW OTHERWISE IT'S HARD TO MANAGE EXPORT/IMPORT DELETION BECAUSE OF DEPENDENCIES
        # self.database.db_from_snapshot_security_group.add_ingress_rule(
        #     self.function_security_group,
        #     ec2.Port.tcp(3306),
        #     description=f"Allow inbound traffic from MessageEndpointFunction on port 3306"
        # )

        # !!! USE EXPLICIT CFN OUTPUT & Fn.import_value in OTHER TEMPLATES (DB TEMPLATES FOR EXAMPLE)
        CfnOutput(self, "MessageEndpointFunctionSecurityGroup",
            value=self.function_security_group.security_group_id,
            export_name="MessageEndpointFunctionSecurityGroup"
        )

        bedrock_access_policy = iam.ManagedPolicy(self, "BedrockAccessPolicy",
            managed_policy_name="BedrockAccessPolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[ 
                            "bedrock:InvokeModel",
                    ],
                    resources=[
                        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
                        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                        "arn:aws:bedrock:us-east-1::foundation-model/cohere.embed-english-v3"
                    ]
                )
            ]
        )

        self.function.role.add_managed_policy(bedrock_access_policy)   
         
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
