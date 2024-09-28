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

    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, network: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.network = network

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
                        "bedrock:GetAgentVersion",
                        "bedrock:ListDataSources",
                        "bedrock:ListModelInvocationJobs",
                        "bedrock:ListTagsForResource",
                        "bedrock:GetAgent",
                        "bedrock:GetDataSource",
                        "bedrock:DetectGeneratedContent",
                        "bedrock:UntagResource",
                        "bedrock:ListAgents",
                        "bedrock:GetEvaluationJob",
                        "bedrock:GetModelEvaluationJob",
                        "bedrock:ListAgentVersions",
                        "bedrock:GetModelCopyJob",
                        "bedrock:ListCustomModels",
                        "bedrock:GetModelInvocationJob",
                        "bedrock:GetModelImportJob",
                        "bedrock:Retrieve",
                        "bedrock:InvokeModel",
                        "bedrock:GetAgentAlias",
                        "bedrock:GetAgentMemory",
                        "bedrock:ListFoundationModelAgreementOffers",
                        "bedrock:GetIngestionJob",
                        "bedrock:ListModelImportJobs",
                        "bedrock:GetFlowAlias",
                        "bedrock:ListFlows",
                        "bedrock:ListInferenceProfiles",
                        "bedrock:ApplyGuardrail",
                        "bedrock:GetFlowVersion",
                        "bedrock:ListAgentActionGroups",
                        "bedrock:ListProvisionedModelThroughputs",
                        "bedrock:ListAgentAliases",
                        "bedrock:GetFlow",
                        "bedrock:GetGuardrail",
                        "bedrock:GetFoundationModelAvailability",
                        "bedrock:GetKnowledgeBase",
                        "bedrock:InvokeFlow",
                        "bedrock:GetModelInvocationLoggingConfiguration",
                        "bedrock:GetInferenceProfile",
                        "bedrock:GetPrompt",
                        "bedrock:ListPrompts",
                        "bedrock:ListKnowledgeBases",
                        "bedrock:InvokeModelWithResponseStream",
                        "bedrock:ListFlowVersions",
                        "bedrock:ListFlowAliases",
                        "bedrock:ListModelCustomizationJobs",
                        "bedrock:ListModelCopyJobs",
                        "bedrock:ListGuardrails",
                        "bedrock:ListImportedModels",
                        "bedrock:ListAgentKnowledgeBases",
                        "bedrock:GetCustomModel",
                        "bedrock:GetResourcePolicy",
                        "bedrock:GetImportedModel",
                        "bedrock:GetUseCaseForModelAccess",
                        "bedrock:ListModelEvaluationJobs",
                        "bedrock:ListIngestionJobs",
                        "bedrock:ListEvaluationJobs",
                        "bedrock:GetAgentActionGroup",
                        "bedrock:GetModelCustomizationJob",
                        "bedrock:GetAgentKnowledgeBase",
                        "bedrock:InvokeAgent",
                        "bedrock:TagResource",
                        "bedrock:GetFoundationModel",
                        "bedrock:GetProvisionedModelThroughput",
                        "bedrock:ListFoundationModels"
                    ],
                    resources=[
                        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
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

        # create an ec2 instance
        self.instance = ec2.Instance(self, "LLMServerInstance",
            instance_name="LLMServerInstance",
            vpc = self.network.vpc,
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
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
            ),
            role=role,
            security_group=self.security_group,
            private_ip_address='10.0.190.145'
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