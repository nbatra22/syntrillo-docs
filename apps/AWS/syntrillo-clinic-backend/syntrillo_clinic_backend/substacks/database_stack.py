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
    aws_iam as iam,
)
from constructs import Construct

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class DatabaseStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, network: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.network = network

        removal_policy_value = self.environment_context["database"]["removal-policy"]
        self.removal_policy = RemovalPolicy[removal_policy_value]

        self.snapshot_identifier = self.environment_context["database"]["snapshot-identifier"]

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
                "log_output": "FILE"
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

        # Create Database
        self.db_from_snapshot = rds.DatabaseInstanceFromSnapshot(self, "MySQLDatabaseFromSnapshot",
            vpc=self.network.vpc,
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_35),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc_subnets=ec2.SubnetSelection(subnets=self.network.vpc.private_subnets),
            multi_az=False,
            allocated_storage=20,
            storage_type=rds.StorageType.GP3,
            removal_policy=self.removal_policy,
            snapshot_identifier=self.snapshot_identifier,
            credentials=rds.SnapshotCredentials.from_generated_secret("admin"),
            parameter_group=parameter_group,
            monitoring_interval=Duration.seconds(60),
            monitoring_role=enhanced_monitoring_role,
        )

        # Allow Database Access
        self.db_from_snapshot_security_group = self.db_from_snapshot.connections.security_groups[0]

        private_subnet_cidr_blocks = [subnet.ipv4_cidr_block for subnet in self.network.vpc.private_subnets]

        for cidr_block in private_subnet_cidr_blocks:
            self.db_from_snapshot_security_group.add_ingress_rule(
                ec2.Peer.ipv4(cidr_block),
                ec2.Port.tcp(3306),
                description=f"Allow inbound traffic from {cidr_block} on port 3306"
            )

        self.admin_secret = self.db_from_snapshot.secret

        self.db_from_snapshot_security_group.add_ingress_rule(
            self.network.bastion_host_security_group,
            ec2.Port.tcp(3306),
            description=f"Allow inbound traffic from Linux Bastion Host on port 3306"
        )