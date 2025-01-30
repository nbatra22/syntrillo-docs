from constructs import Construct
from aws_cdk import (
    Stack,
    Fn,
    aws_dms as dms,
    aws_iam as iam,
    aws_logs as logs,
    aws_ec2 as ec2,
    SecretValue,
    aws_secretsmanager as secretsmanager,
    aws_s3 as s3
)

class IngestionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, network: Construct, storage: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.environment_name = self.environment_context["environment-name"]

        self.vpc = network.vpc
        self.storage = storage

        raw_data_bucket_name = Fn.import_value("RawDataBucketName")
        # raw_data_bucket_arn = Fn.import_value("RawDataBucketArn")

        dms_instance_security_group = Fn.import_value("SyntrilloAnalyticsNetworkDMSSecurityGroupId")

        # create bucket object from bucket name raw_data_bucket
        raw_data_bucket = s3.Bucket.from_bucket_name(self, "IngestionRawDataBucket", bucket_name=raw_data_bucket_name)

        # Create DMS replication instance and endpoints
        dms_vpc_role = iam.Role(
            self, "DMSVpcRole",
            assumed_by=iam.ServicePrincipal("dms.us-east-1.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonDMSVPCManagementRole"),
            ],
            role_name="dms-vpc-role"
        )

        # Create DMS CloudWatch Logs Role
        dms_cloudwatch_logs_role = iam.Role(
            self, "DmsCloudWatchLogsRole",
            role_name="dms-cloudwatch-logs-role",  # This specific name is required by DMS
            assumed_by=iam.ServicePrincipal("dms.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonDMSCloudWatchLogsRole"
                )
            ]
        )

        # dms_role = iam.Role(
        #     self, "DMSRole",
        #     assumed_by=iam.ServicePrincipal("dms.amazonaws.com"),
        #     managed_policies=[
        #         iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonDMSCloudWatchLogsRole"),
        #         iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        #     ]
        # )

        # dms_role.add_to_policy(iam.PolicyStatement(
        #     actions=["s3:*"],
        #     resources=["arn:aws:s3:::staging.syntrillo-analytics.raw-data/*"]
        # ))

        s3_target_endpoint_role = iam.Role(
            self, "DMSS3Role",
            assumed_by=iam.ServicePrincipal("dms.us-east-1.amazonaws.com")
        )

        s3_target_endpoint_role.add_to_policy(iam.PolicyStatement(
            actions=[ 
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:PutObjectTagging"
            ],
            resources=[
                f"{raw_data_bucket.bucket_arn}", 
                f"{raw_data_bucket.bucket_arn}/*"
            ]
        ))

        # raw_data_bucket.grant_read_write(s3_target_endpoint_role)

        self.subnet_ids = [
            Fn.import_value("SyntrilloAnalyticsNetworkIsolatedSubnetId-1"),
            Fn.import_value("SyntrilloAnalyticsNetworkIsolatedSubnetId-2"),
        ]


        # !! There is a dependcy with dms-vpc-role, and this role must have this name (dms-vpc-role), the cdk template therefore should be executed in 2 times (because there is no depends on apprently)
        dms_subnet_group = dms.CfnReplicationSubnetGroup(
            self, "DMSSubnetGroup",
            replication_subnet_group_description="DMS subnet group",
            subnet_ids=self.subnet_ids
        )
        # Add explicit dependency on the DMS VPC role
        dms_subnet_group.node.add_dependency(dms_vpc_role)
        
        # Create replication instance
        dms_instance = dms.CfnReplicationInstance(
            self, "DMSInstance",
            replication_instance_class="dms.t3.micro",
            allocated_storage=50,
            publicly_accessible=False,
            replication_subnet_group_identifier=dms_subnet_group.ref,
            vpc_security_group_ids=[dms_instance_security_group]
        )

        database_certificate = Fn.import_value("DatabaseCertificateSecretArn")

        # Get the certificate from Secrets Manager
        certificate_secret = secretsmanager.Secret.from_secret_complete_arn(
            self, "DatabaseCertificateSecret",
            secret_complete_arn=database_certificate
        )

        # Create the certificate
        certificate = dms.CfnCertificate(
            self, "DMSCertificate",
            certificate_identifier="syntrillo-clinic-database-certificate",
            certificate_pem=certificate_secret.secret_value.unsafe_unwrap()
        )

        # # Create source endpoint (MySQL)
        # source_endpoint = dms.CfnEndpoint(
        #     self, "SourceEndpoint", 
        #     endpoint_type="source",
        #     engine_name="mysql",
        #     server_name="syntrilloclinicbackendsta-mysqldatabasefromsnapsho-saiukm5mugdm.cv68uwgwk82p.us-east-1.rds.amazonaws.com",
        #     port=3306,
        #     database_name="syntrillo$HealthInformation",
        #     username="syntrillo_analytics_dms_user",
        #     password="^9T8Bs46PezZuFAg",
        #     ssl_mode="verify-full",
        #     certificate_arn=certificate.ref 
        # )

        # Import the secret ARN from the other stack
        secret_arn = Fn.import_value("DatabaseDMSUserSecretsArn")
        secrets_kms_custom_key_arn = Fn.import_value("SecretsCutomKMSKeyArn")

        # Create IAM role for DMS to access Secrets Manager
        dms_secret_role = iam.Role(self, "DMSSecretRole",
            assumed_by=iam.ServicePrincipal("dms.us-east-1.amazonaws.com"),
            description="Role for DMS to access Secrets Manager"
        )

        # Add policy to allow DMS to read the secret
        dms_secret_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret",
            ],
            resources=[secret_arn]
        ))

        dms_secret_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "kms:Decrypt",
            ],
            resources=[secrets_kms_custom_key_arn]
        ))

        # Create source endpoint (MySQL)
        source_endpoint = dms.CfnEndpoint(
            self, "SourceEndpoint", 
            endpoint_type="source",
            engine_name="mysql",
            ssl_mode="verify-full",
            certificate_arn=certificate.ref,
            my_sql_settings=dms.CfnEndpoint.MySqlSettingsProperty(
                secrets_manager_secret_id=secret_arn,
                secrets_manager_access_role_arn=dms_secret_role.role_arn,
            )
        )

        # Create target endpoint (S3)
        target_endpoint = dms.CfnEndpoint(
            self, "TargetEndpoint",
            endpoint_type="target",
            engine_name="s3",
            extra_connection_attributes="IncludeOpForFullLoad=true",
            s3_settings=dms.CfnEndpoint.S3SettingsProperty(
                bucket_name=raw_data_bucket_name,
                service_access_role_arn=s3_target_endpoint_role.role_arn
            )
        )

        # Create replication task
        dms.CfnReplicationTask(
            self, "ReplicationTask",
            replication_instance_arn=dms_instance.ref,
            migration_type="full-load-and-cdc",
            source_endpoint_arn=source_endpoint.ref,
            target_endpoint_arn=target_endpoint.ref,
            table_mappings='''
            {
                "rules": [
                {
                    "rule-type": "selection",
                    "rule-id": "1",
                    "rule-name": "1",
                    "object-locator": {
                        "schema-name": "syntrillo$HealthInformation",
                        "table-name": "tenovi_raw_measurements"
                    },
                    "rule-action": "include"
                },
                {
                    "rule-type": "transformation",
                    "rule-id": "2",
                    "rule-name": "Remove json column",
                    "rule-action": "remove-column",
                    "rule-target": "column",
                    "object-locator": {
                        "schema-name": "syntrillo$HealthInformation",
                        "table-name": "tenovi_raw_measurements",
                        "column-name": "data_json"
                    }
                }
                ]
            }
            ''',
            replication_task_settings='''
            {
                "Logging": {
                    "EnableLogging": true
                }
            }
            '''
        )


        # # Create CloudWatch Log Group
        # log_group = logs.LogGroup(
        #     self, "DmsLogGroup",
        #     log_group_name=f"dms-task-3XEXYCS4HBH45HOPQR7L5EZCEI",
        #     retention=logs.RetentionDays.ONE_WEEK,
        #     # removal_policy=RemovalPolicy.DESTROY
        # )

        # # log_group = logs.LogGroup(
        # #     self, "DmsLogGroup2",
        # #     log_group_name=f"dms-tasks-dmsinstance-wtosx3dsrbmpeyls",
        # #     retention=logs.RetentionDays.ONE_WEEK,
        # #     # removal_policy=RemovalPolicy.DESTROY
        # # )