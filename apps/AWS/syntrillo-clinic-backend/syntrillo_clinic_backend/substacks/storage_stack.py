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
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class StorageStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, network, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.network = network

        self.termination_protection = self.environment_context["stacks-termination-protection"]

        removal_policy_value = self.environment_context["storage"]["removal-policy"]
        self.removal_policy = RemovalPolicy[removal_policy_value]
        
        self.efs_file_system = efs.FileSystem(self, "SyntrilloClinicEFS",
            vpc=self.network.vpc,
            removal_policy=self.removal_policy
        )

        self.efs_access_point = efs.AccessPoint(self, "SyntrilloClinicEFSAccessPoint",
            file_system=self.efs_file_system,
            path="/shared-python-modules", # !! THIS MUST EXIST ON EFS FOR THE LAMBDA TO WORK
            posix_user=efs.PosixUser(
                uid="1001",
                gid="1001"
            )
        )

        self.efs_access_point_chatbots = efs.AccessPoint(self, "SyntrilloClinicEFSAccessPointChatbots",
            file_system=self.efs_file_system,
            path="/chatbots-resources", # !! THIS MUST EXIST ON EFS FOR THE LAMBDA TO WORK
            create_acl=efs.Acl(
                owner_uid="1000",
                owner_gid="1000",
                permissions="750"
            ),
            posix_user=efs.PosixUser(
                uid="1000",
                gid="1000"
            )
        )

        CfnOutput(self, "EFSAccessPointChatbotsArn",
            value=self.efs_access_point_chatbots.access_point_arn,
            export_name="EFSAccessPointChatbotsArn"
        )

        CfnOutput(
            self,
            "SyntrilloClinicEFSFileStystemId",
            value=self.efs_file_system.file_system_id,
            export_name="SyntrilloClinicEFSFileStystemId"
        )

        # ALLOW BASTION HOST TO ACCESS EFS FILE SYSTEM
        self.efs_security_group = self.efs_file_system.connections.security_groups[0]

        self.efs_security_group.add_ingress_rule(
            peer=self.network.bastion_host_security_group,
            connection=ec2.Port.tcp(2049),
            description="Allow NFS from bastion host"
        )