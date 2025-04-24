from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    Fn,
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
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
)
from constructs import Construct

class BloodPressureNotificationFunction(Construct):
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

        # ---------------------------------------------------------------------
        # INPUTS
        # ---------------------------------------------------------------------

        self.secrets_database_lambda_user_secrets_secret_arn = Fn.import_value("SyntrilloClinic-Secrets-Database-LambdaUserSecrets-Arn")
        self.secrets_tenovi_hwi_secrets_secret_arn = Fn.import_value("SyntrilloClinic-Secrets-TenoviHwiSecrets-Arn")
        self.secrets_healthie_secrets_secret_arn = Fn.import_value("SyntrilloClinic-Secrets-HealthieSecrets-Arn")
        self.secrets_secrets_kms_key_arn = Fn.import_value("SyntrilloClinic-Secrets-SecretsKMSKey-Arn")

        self.clinic_storage_efs_file_system_id = Fn.import_value("SyntrilloClinic-Storage-EFS-FileSystem-Id")
        self.clinic_storage_efs_access_point_shared_python_modules_arn = Fn.import_value("SyntrilloClinic-Storage-EFS-AccessPoint-SharedPythonModules-Arn")
        self.clinic_storage_efs_file_system_security_group_id = Fn.import_value("SyntrilloClinic-Storage-EFS-FileSystem-SecurityGroup-Id")

        # Import file system endpoint

        file_system_security_group = ec2.SecurityGroup.from_security_group_id(
            self,
            "ImportedFileSystemSecurityGroup",
            security_group_id=self.clinic_storage_efs_file_system_security_group_id
        )

        imported_file_system = efs.FileSystem.from_file_system_attributes(
            self,
            "ImportedFileSystem",
            file_system_id=self.clinic_storage_efs_file_system_id,
            security_group=file_system_security_group
        )

        self.clinic_storage_efs_access_point_shared_python_modules = efs.AccessPoint.from_access_point_attributes(
            self,
            "EFSAccessPoint",
            access_point_arn=self.clinic_storage_efs_access_point_shared_python_modules_arn,
            file_system=imported_file_system
        )

        self.secrets_openai_secrets_secret_arn = ''

        self.vpc = ec2.Vpc.from_vpc_attributes(self, "ImportedVpc",
            vpc_id=Fn.import_value("SyntrilloClinic-Network-Vpc-Id"),
            availability_zones=[Fn.import_value("SyntrilloClinic-Network-Vpc-AvailabilityZone-0"), Fn.import_value("SyntrilloClinic-Network-Vpc-AvailabilityZone-1")],
            private_subnet_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet1-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet2-Id")],
            public_subnet_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet1-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet2-Id")],
            private_subnet_route_table_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet1-RouteTable-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet2-RouteTable-Id")],
            public_subnet_route_table_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet1-RouteTable-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet2-RouteTable-Id")]
        )

        # ---------------------------------------------------------------------   

        params_and_secrets = _lambda.ParamsAndSecretsLayerVersion.from_version(_lambda.ParamsAndSecretsVersions.V1_0_103,
            cache_size=500,
            log_level=_lambda.ParamsAndSecretsLogLevel.NONE
        )

        self.function = _lambda.Function(self, "BloodPressureNotificationFunction",
            function_name="BloodPressureNotificationFunction",
            vpc = self.vpc,
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda-functions/blood-pressure-notification-function", exclude=['.env', '__pycache__']),
            params_and_secrets=params_and_secrets,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.clinic_storage_efs_access_point_shared_python_modules,
                "/mnt/python_modules"
            ),
            environment={
                "POWERTOOLS_LOG_LEVEL": self.environment_context['blood_pressure_notification_function']['log_level'],
                "PYTHONPATH": "/mnt/python_modules",
                "AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN": self.secrets_database_lambda_user_secrets_secret_arn,
                "AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN": self.secrets_tenovi_hwi_secrets_secret_arn,
                "AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN": self.secrets_healthie_secrets_secret_arn,
                "AWS_SECRETS_MANAGER_OPENAI_SECRET_ARN": self.secrets_openai_secrets_secret_arn,
                "AWS_ENVIRONMENT": ssm.StringParameter.from_string_parameter_name(
                    self,
                    "SyntrilloClinicAWSEnvironment",
                    string_parameter_name="/syntrillo-clinic/aws/environment"
                ).string_value
            },
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=self.environment_context['blood_pressure_notification_function']['memory_size'], 
            timeout=Duration.seconds(self.environment_context['blood_pressure_notification_function']['lambda_time_out_seconds']),
            reserved_concurrent_executions=self.environment_context['blood_pressure_notification_function']['reserved_concurrent_executions']
        )

        self.function_alias = _lambda.Alias(
            self, "LambdaAlias",
            alias_name="provisionned-concurrency",
            version=self.function.current_version,
            provisioned_concurrent_executions=self.environment_context['blood_pressure_notification_function']['provisioned_concurrency_executions']
        )

        self.grant_read_secrets(self.secrets_database_lambda_user_secrets_secret_arn, self.secrets_secrets_kms_key_arn)
        self.grant_read_secrets(self.secrets_tenovi_hwi_secrets_secret_arn, self.secrets_secrets_kms_key_arn)
        self.grant_read_secrets(self.secrets_healthie_secrets_secret_arn, self.secrets_secrets_kms_key_arn)
        # self.grant_read_secrets(self.secrets_openai_secrets_secret_arn, self.secrets_secrets_kms_key_arn)

        self.function_security_group = self.function.connections.security_groups[0]

        # self.database.db_from_snapshot_security_group.add_ingress_rule(
        #     self.function_security_group,
        #     ec2.Port.tcp(3306),
        #     description=f"Allow inbound traffic from BloodPressureNotificationFunction on port 3306"
        # )

        # self.database.db_from_snapshot_security_group.add_ingress_rule(
        #     self.function_security_group,
        #     ec2.Port.tcp(3306),
        #     description=f"Allow inbound traffic from IFrameGeneratorFunction on port 3306"
        # )

        # ---------------------------------------------------------------------
        # OUTPUTS
        # ---------------------------------------------------------------------

        CfnOutput(self, "SyntrilloClinicServersBloodPressureNotificationFunctionSecurityGroupId",
            value=self.function_security_group.security_group_id,
            export_name="SyntrilloClinic-Servers-BloodPressureNotificationFunction-SecurityGroup-Id"
        )        
    
    def grant_read_secrets(self, secrets_arn, secrets_kms_key_arn):
        # Must be used instead of grant_read to avoid circular dependency (n.b.: No real explanation why it creates a circular dependency)
        self.function.add_to_role_policy(iam.PolicyStatement(
            actions=["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue"],
            resources=[secrets_arn],
        ))
        self.function.add_to_role_policy(iam.PolicyStatement(
            actions=["kms:Decrypt"],
            resources=[secrets_kms_key_arn],
        ))
