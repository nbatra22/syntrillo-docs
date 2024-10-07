from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct

class SyntrilloGenaiBackendSandboxStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self, "SyntrilloGenAiBackendSandboxVPC",
            vpc_name = "SyntrilloGenAiBackendSandboxVPC",
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC)
            ]
        )

        role = iam.Role(self, "EC2SSMRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        bedrock_access_policy = iam.ManagedPolicy.from_managed_policy_arn(self, "BedrockSandboxAccessPolicy", 
            managed_policy_arn="arn:aws:iam::730335351683:policy/BedrockSandboxAccess"
        )
        role.add_managed_policy(bedrock_access_policy)

        cloudwatch_access_policy = iam.ManagedPolicy.from_managed_policy_arn(self, "CloudwatchAccessPolicy", 
            managed_policy_arn="arn:aws:iam::730335351683:policy/ClouwatchLogsSSMLogGroupAccess"
        )
        role.add_managed_policy(cloudwatch_access_policy)

        # Create a security group
        security_group = ec2.SecurityGroup(self, "UbuntuInstanceSG",
            vpc=self.vpc,
            description="Security group for Ubuntu EC2 instance",
            allow_all_outbound=True
        )

        # create an ec2 instance
        self.instance = ec2.Instance(self, "SyntrilloGenAiBackendSandboxInstance",
            instance_name="SyntrilloGenAiBackendSandboxInstance",
            vpc = self.vpc,
            instance_type=ec2.InstanceType("t3.micro"),
            # machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            # machine_image=ec2.MachineImage.from_ssm_parameter(
            #     "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id",
            #     os=ec2.OperatingSystemType.LINUX
            # ),
            machine_image = ec2.MachineImage.generic_linux({
                "us-east-1": "ami-04a98573e58903ee0",
            }),
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            role=role,
            security_group=security_group,
        )
