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
    aws_iam as iam,
)
from constructs import Construct

class LLMServer(Construct):

    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, network: Construct, database: Construct, iframe_generator_function: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.network = network
        self.database = database
        self.iframe_generator_function = iframe_generator_function

        role = iam.Role(self, "EC2SSMRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        # Create a policy
        bedrock_access_policy = iam.ManagedPolicy(self, "BedrockSandboxAccessPolicy",
            managed_policy_name="BedrockSandboxAccessPolicy",
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

        # bedrock_access_policy = iam.ManagedPolicy.from_managed_policy_arn(self, "BedrockSandboxAccessPolicy", 
        #     managed_policy_arn="arn:aws:iam::730335351683:policy/BedrockSandboxAccess"
        # )
        # role.add_managed_policy(bedrock_access_policy)

        role.add_managed_policy(bedrock_access_policy)

        cloudwatch_access_policy = iam.ManagedPolicy(self, "SSMSessionManagerLogGroupAccess",
            managed_policy_name="SSMSessionManagerLogGroupAccess",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogGroup",
                    ],
                    resources=["arn:aws:logs:us-east-1:730335351683:log-group:/aws/ssm/session-manager"]
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogStreams"
                    ],
                    resources=["arn:aws:logs:us-east-1:730335351683:log-group:/aws/ssm/session-manager:log-stream:*"]
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[ 
                        "logs:DescribeLogGroups",
                    ],
                    resources=["*"]
                )
            ]
        )

        # cloudwatch_access_policy = iam.ManagedPolicy.from_managed_policy_arn(self, "CloudwatchAccessPolicy", 
        #     managed_policy_arn="arn:aws:iam::730335351683:policy/ClouwatchLogsSSMLogGroupAccess"
        # )

        role.add_managed_policy(cloudwatch_access_policy)

        s3_access_policy = iam.ManagedPolicy(self, "S3Access",
            managed_policy_name="S3Access",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                    ],
                    resources=[f"arn:aws:s3:::{environment_context['environment_name']}.syntrillo-clinic-backend.llm-server-packages/llm-service.zip"]
                ),
            ]
        )

        # cloudwatch_access_policy = iam.ManagedPolicy.from_managed_policy_arn(self, "CloudwatchAccessPolicy", 
        #     managed_policy_arn="arn:aws:iam::730335351683:policy/ClouwatchLogsSSMLogGroupAccess"
        # )

        role.add_managed_policy(s3_access_policy)

        if self.environment_context['environment_name'] == "sandbox":
            secrets_manager_access_policy = iam.ManagedPolicy(self, "SecretsManagerAccess",
                managed_policy_name="SecretsManagerAccess",
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "secretsmanager:GetSecretValue",
                        ],
                        resources=[f"arn:aws:secretsmanager:us-east-1:730335351683:secret:DatabaseAdminSecrets4B85717-UlIzzA9DkHCH-Ma6zBE"]
                    ),
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=[
                            "kms:Decrypt",
                        ],
                        resources=[f"arn:aws:kms:us-east-1:730335351683:key/c6479b30-673f-4518-8856-213eb2df0c6a"]
                    ),
                ]
            )

            # cloudwatch_access_policy = iam.ManagedPolicy.from_managed_policy_arn(self, "CloudwatchAccessPolicy", 
            #     managed_policy_arn="arn:aws:iam::730335351683:policy/ClouwatchLogsSSMLogGroupAccess"
            # )

            role.add_managed_policy(secrets_manager_access_policy)


        # Create a security group
        self.security_group = ec2.SecurityGroup(self, "UbuntuInstanceSG",
            vpc=self.network.vpc,
            description="Security group for LLM Server",
            allow_all_outbound=True
        )

        # security_group.add_ingress_rule(
        #     ec2.Peer.any_ipv4(),
        #     ec2.Port.tcp(443),
        #     "Allow LLM server access httpS"
        # )

        # security_group.add_ingress_rule(
        #     ec2.Peer.any_ipv4(),
        #     ec2.Port.tcp(80),
        #     "Allow LLM server access http"
        # ) 

        # # create an ec2 instance
        # self.instance = ec2.Instance(self, "LLMServerInstance",
        #     instance_name="LLMServerInstance",
        #     vpc = self.network.vpc,
        #     instance_type=ec2.InstanceType("t3.micro"),
        #     # machine_image=ec2.MachineImage.latest_amazon_linux2023(),
        #     # machine_image=ec2.MachineImage.from_ssm_parameter(
        #     #     "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id",
        #     #     os=ec2.OperatingSystemType.LINUX
        #     # ),
        #     machine_image = ec2.MachineImage.generic_linux({
        #         "us-east-1": "ami-04a98573e58903ee0",
        #     }),
        #     vpc_subnets=ec2.SubnetSelection(
        #         subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
        #     ),
        #     role=role,
        #     security_group=self.security_group,
        #     private_ip_address='10.0.190.145'
        # )

        # create an ec2 instance
        instance_size = self.environment_context["llm_server"]["llm-server-instance-size"]
        ami_id = self.environment_context["llm_server"]["llm-server-ami-id"]
        self.instance_linux_2023 = ec2.Instance(self, "LLMServerInstance2023",
            instance_name="LLMServerInstance2023",
            vpc = self.network.vpc,
            instance_type=ec2.InstanceType(instance_size),
            # machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            # machine_image=ec2.MachineImage.from_ssm_parameter(
            #     "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id",
            #     os=ec2.OperatingSystemType.LINUX
            # ),
            machine_image = ec2.MachineImage.generic_linux({
                "us-east-1": ami_id,
            }),
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            ),
            role=role,
            security_group=self.security_group,
            private_ip_address='10.0.190.146'
        )

        self.security_group.add_ingress_rule(
            self.iframe_generator_function.function_security_group,
            ec2.Port.tcp(443),
            "Allow LLM server access httpS"
        )

        self.security_group.add_ingress_rule(
            self.iframe_generator_function.function_security_group,
            ec2.Port.tcp(80),
            "Allow LLM server access http"
        )

        if self.environment_context['environment_name'] == "sandbox":
            self.database.db_from_snapshot_security_group.add_ingress_rule(
                self.security_group,
                ec2.Port.tcp(3306),
                description=f"Allow inbound traffic from LLM Server on port 3306"
            )

        # Create a security group for the VPC Endpoint
        security_group = ec2.SecurityGroup(
            self, "BedrockEndpointSG",
            vpc=self.network.vpc,
            description="Security Group for Bedrock VPC Endpoint",
            allow_all_outbound=True
        )

        # Allow inbound HTTPS traffic from the VPC
        security_group.add_ingress_rule(
            ec2.Peer.ipv4(self.network.vpc.vpc_cidr_block),
            ec2.Port.tcp(443),
            "Allow HTTPS inbound from VPC"
        )

        bedrock_endpoint = ec2.InterfaceVpcEndpoint(
            self, "BedrockVPCEndpoint",
            vpc=self.network.vpc,
            service=ec2.InterfaceVpcEndpointService("com.amazonaws.us-east-1.bedrock-runtime"),
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[security_group]
        )        