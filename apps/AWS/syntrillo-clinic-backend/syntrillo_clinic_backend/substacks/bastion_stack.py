from aws_cdk import (
    Stack,
    Duration,
    CfnTag,
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

class SyntrilloClinicBastionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, network: Construct, storage: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.network = network
        self.storage = storage

        security_group = ec2.SecurityGroup(
            self,
            id="bastion_security_group",
            vpc=self.network.vpc,
        )

        # Create the bastion host
        bastion_host = ec2.BastionHostLinux(
            self, "BastionHost",
            vpc=self.network.vpc,
            instance_type=ec2.InstanceType("t3.micro"),
            subnet_selection=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            security_group=security_group
        )

        # Get the security group associated with the EFS file system
        efs_security_group = self.storage.efs_file_system.connections.security_groups[0]

        # Allow NFS traffic from the bastion host to the EFS file system
        efs_security_group.add_ingress_rule(
            peer=security_group,
            connection=ec2.Port.tcp(2049),
            description="Allow NFS from bastion host"
        )