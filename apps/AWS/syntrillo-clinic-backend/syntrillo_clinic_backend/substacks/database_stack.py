from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
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
    aws_kms as kms,
    aws_iam as iam,
    aws_logs as logs,
    
)
from constructs import Construct

import json
# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class DatabaseStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, network: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------------------------------------------------------------------
        # INPUTS
        # ---------------------------------------------------------------------
        self.environment_context = environment_context
        self.aws_environment = environment_context["environment_name"]

        self.network = network

        self.termination_protection = self.environment_context["stacks-termination-protection"]

        removal_policy_value = self.environment_context["database"]["removal-policy"]
        self.removal_policy = RemovalPolicy[removal_policy_value]

        self.snapshot_identifier = self.environment_context["database"]["snapshot-identifier"]

        self.vpc = ec2.Vpc.from_vpc_attributes(self, "ImportedVpc",
            vpc_id=Fn.import_value("SyntrilloClinic-Network-Vpc-Id"),
            availability_zones=[Fn.import_value("SyntrilloClinic-Network-Vpc-AvailabilityZone-0"), Fn.import_value("SyntrilloClinic-Network-Vpc-AvailabilityZone-1")],
            private_subnet_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet1-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet2-Id")],
            public_subnet_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet1-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet2-Id")],
            private_subnet_route_table_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet1-RouteTable-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet2-RouteTable-Id")],
            public_subnet_route_table_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet1-RouteTable-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet2-RouteTable-Id")]
        )

        # ---------------------------------------------------------------------
        # Create Database
        # ---------------------------------------------------------------------

        # Create databse encryption key
        rds_encryption_key = kms.Key(self, "SyntrilloClinicMySQLDatabaseEncryptionKey",
            description="Syntrillo Clinic MySQL Database Encyption Key",
            enabled=True,
            enable_key_rotation=True
        )

        # Enable logging in a parameter group
        parameter_group = rds.ParameterGroup(self, "MySQLDatabaseFromSnapshotParameterGroup",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0_35
            ),
            parameters={
                "general_log": "1",
                "slow_query_log": "1",
                "long_query_time": "2",  # Logs queries longer than 2 seconds
                "log_output": "FILE",
                "require_secure_transport": "ON",  # Enforce SSL/TLS
                "binlog_format": "ROW",     # Necessary for 
                "binlog_row_image": "FULL"

            }
        )

        # Enable enhanced monitoring
        enhanced_monitoring_role = iam.Role(
            self, "MySQLDatabaseFromSnapshotEnhancedMonitoringRole",
            assumed_by=iam.ServicePrincipal("monitoring.rds.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonRDSEnhancedMonitoringRole")
            ]
        )

        # Create database from snasphsot
        self.db_from_snapshot = rds.DatabaseInstanceFromSnapshot(self, "MySQLDatabaseFromSnapshot",
            vpc=self.vpc,
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_35),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc_subnets=ec2.SubnetSelection(subnets=self.vpc.private_subnets),
            multi_az=False,
            allocated_storage=20,
            storage_type=rds.StorageType.GP3,
            removal_policy=self.removal_policy,
            snapshot_identifier=self.snapshot_identifier,
            # credentials=rds.SnapshotCredentials.from_generated_secret("admin"),
            parameter_group=parameter_group,
            monitoring_interval=Duration.seconds(60),
            monitoring_role=enhanced_monitoring_role,
            iam_authentication=True,
            cloudwatch_logs_exports=["error", "general", "slowquery", "audit"],
        )

        # ---------------------------------------------------------------------
        # Create Database Credentials
        # ---------------------------------------------------------------------
        self.database_admin_secrets = secretsmanager.Secret(
            self, "DatabaseAdminSecrets",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({
                    "username": "admin",
                    "host": self.db_from_snapshot.instance_endpoint.hostname
                }),
                generate_string_key="password",
                exclude_characters='/@"\\',
                include_space=False,
                password_length=32
            ),
            encryption_key=rds_encryption_key
        )

        self.db_from_snapshot.credentials = rds.Credentials.from_secret(self.database_admin_secrets)

        # ---------------------------------------------------------------------
        # Create SSM String Parameter ???
        # ---------------------------------------------------------------------
        db_host_param = ssm.StringParameter(
            self,
            "DatabaseHostParameter",
            parameter_name="/syntrillo-clinic/aws/db/host",
            string_value=self.db_from_snapshot.instance_endpoint.hostname,
            description="Database host",
        )

        # ---------------------------------------------------------------------
        # Create Encrypted Database Logs
        # ---------------------------------------------------------------------
        instance_id = self.db_from_snapshot.instance_identifier

        log_encryption_key = kms.Key(self, "RDSLogEncryptionKey",
            description="KMS key for RDS log encryption",
            enable_key_rotation=True
        )

        log_encryption_key.grant_encrypt_decrypt(iam.ServicePrincipal("logs.amazonaws.com"))
        
        for log_type in ["error", "general", "slowquery", "audit"]:
            log_group_name = f"/aws/rds/instance/{instance_id}/{log_type}"
            log_group = logs.LogGroup(
                self, 
                f"LogGroup{log_type.capitalize()}", 
                log_group_name=log_group_name,
                retention=logs.RetentionDays.ONE_MONTH,
                encryption_key=log_encryption_key,
                removal_policy=RemovalPolicy.DESTROY
            )
            log_group_arn = log_group.log_group_arn

            log_encryption_key.grant_encrypt_decrypt(iam.ServicePrincipal("rds.amazonaws.com"))
        
        # ---------------------------------------------------------------------
        # Add ingress rules to database security group
        # ---------------------------------------------------------------------
        self.db_from_snapshot_security_group = self.db_from_snapshot.connections.security_groups[0]

        # self.admin_secret = self.db_from_snapshot.secret

        def add_security_group_ingress_rule(self, security_group_id, security_group_name, description):
            imported_security_group = ec2.SecurityGroup.from_security_group_id(
                self,
                security_group_name,
                security_group_id=security_group_id
            )
            
            self.db_from_snapshot_security_group.add_ingress_rule(
                imported_security_group,
                ec2.Port.tcp(3306),
                description=f"Allow inbound traffic from {description} on port 3306"
            )

        # Allow Bastion Access
        add_security_group_ingress_rule(
            self,
            Fn.import_value("SyntrilloClinic-Bastion-SecurityGroup-Id"),
            "BastionImportedSecurityGroup",
            "Bastion"
        )

        # Allow Remote Monitoring function Access
        add_security_group_ingress_rule(
            self,
            Fn.import_value("SyntrilloClinic-TaskScheduling-RemoteMonitoringDataSyncFunction-SecurityGroup-Id"),
            "RemoteMonitoringDataSyncFunctionImportedSecurityGroup", 
            "RemoteMonitoringDataSyncFunction"
        )

        # Allow Healthie data ingestor function Access
        add_security_group_ingress_rule(
            self,
            Fn.import_value("SyntrilloClinic-TaskScheduling-HealthieDataIngestor-SecurityGroup-Id"),
            "HealthieDataIngestorFunctionImportedSecurityGroup",
            "HealthieDataIngestorFunction"
        )

        # Allow blood pressure notification function Access
        add_security_group_ingress_rule(
            self,
            Fn.import_value("SyntrilloClinic-Servers-BloodPressureNotificationFunction-SecurityGroup-Id"),
            "BloodPressureNotificationFunction",
            "BloodPressureNotificationFunction"
        )

        # Allow DMS access
        add_security_group_ingress_rule(
            self,
            Fn.import_value("SyntrilloAnalyticsNetworkDMSSecurityGroupId"),
            "DMSInstanceImportedSecurityGroup",
            "Analytics DMS Instance"
        )

        # Allow message endpoint access
        add_security_group_ingress_rule(
            self,
            Fn.import_value("SyntrilloClinic-Servers-MessageEndpointFunction-SecurityGroup-Id"),
            "MessageEndpointFunctionImportedSecurityGroup",
            "MessageEndpointFunction"
        )

        # Allow iframe generator function access
        add_security_group_ingress_rule(
            self,
            Fn.import_value("SyntrilloClinic-Servers-IFrameGeneratorFunction-SecurityGroup-Id"),
            "IframeGeneratorFunctionImportedSecurityGroup",
            "IframeGeneratorFunction"
        )

        # Allow pii data sync function access
        add_security_group_ingress_rule(
            self,
            Fn.import_value("SyntrilloClinic-TaskScheduling-PIIDataSyncFunction-SecurityGroup-Id"),
            "PIIDataSyncFunctionImportedSecurityGroup",
            "PIIDataSyncFunction"
        )

        # Allow candid billing ingestor function access
        add_security_group_ingress_rule(
            self,
            Fn.import_value("SyntrilloClinic-TaskScheduling-CandidBillingIngestor-SecurityGroup-Id"),
            "CandidBillingIngestorFunctionImportedSecurityGroup",
            "CandidBillingIngestorFunction"
        )

        # Allow blood pressure anlysis function access
        add_security_group_ingress_rule(
            self,
            Fn.import_value("SyntrilloClinic-TaskScheduling-BloodPressureAnalysis-SecurityGroup-Id"),
            "BloodPressureAnalysisFunctionImportedSecurityGroup",
            "BloodPressureAnalysisFunction"
        )
