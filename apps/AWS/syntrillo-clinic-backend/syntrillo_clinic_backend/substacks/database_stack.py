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

class DatabaseStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, network: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.network = network

        removal_policy_value = self.environment_context["database"]["removal-policy"]
        self.removal_policy = RemovalPolicy[removal_policy_value]

        self.db = rds.DatabaseInstance(self, "MySQLDatabase",
            vpc=self.network.vpc,
            engine=rds.DatabaseInstanceEngine.MYSQL,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc_subnets=ec2.SubnetSelection(subnets=self.network.vpc.private_subnets),
            multi_az=False,
            allocated_storage=20,
            storage_type=rds.StorageType.GP2,
            credentials=rds.Credentials.from_generated_secret("admin"),
            database_name="syntrillo_clinic_db",
            removal_policy=self.removal_policy
        )

        self.db_security_group = self.db.connections.security_groups[0]

        private_subnet_cidr_blocks = [subnet.ipv4_cidr_block for subnet in self.network.vpc.private_subnets]

        for cidr_block in private_subnet_cidr_blocks:
            self.db_security_group.add_ingress_rule(
                ec2.Peer.ipv4(cidr_block),
                ec2.Port.tcp(3306),
                description=f"Allow inbound traffic from {cidr_block} on port 3306"
            )

        self.secret=self.db.secret

        # AllOW BASTION HOST TO ACCESS MYSQL DB
        self.db_security_group.add_ingress_rule(
            self.network.bastion_host_security_group,
            ec2.Port.tcp(3306),
            description=f"Allow inbound traffic from Linux Bastion Host on port 3306"
        )  