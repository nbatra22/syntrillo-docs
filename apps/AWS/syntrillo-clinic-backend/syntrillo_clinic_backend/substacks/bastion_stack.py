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
    aws_iam as iam
)
from constructs import Construct

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class SyntrilloClinicBastionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, network: Construct, database: Construct, storage: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.network = network
        self.database = database
        self.storage = storage

        bation_host_instance_size = self.environment_context["bastion"]["bastion-instance-size"]

        # Create the bastion host
        bastion_host = ec2.BastionHostLinux(
            self, "BastionHost",
            vpc=self.network.vpc,
            instance_type=ec2.InstanceType(bation_host_instance_size),
            subnet_selection=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            security_group=self.network.bastion_host_security_group,
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
        )

        # Mount efs file system on the bastion host
        efs_file_system_id = self.storage.efs_file_system.file_system_id

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "set -xe",
            "cd /home/ec2-user", 
            "mkdir -p efs",
            f"sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport {efs_file_system_id}.efs.us-east-1.amazonaws.com:/ efs",
            "chown ec2-user:ec2-user efs",
            "yum install -y -q mariadb105",
            "yum install -y -q docker",
            "systemctl start docker",
            "chmod 666 /var/run/docker.sock",
            "usermod -a -G docker ec2-user",
        )
        bastion_host.instance.add_user_data(user_data.render())