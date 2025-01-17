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
    aws_logs as logs, 
)
from constructs import Construct

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------
    
class NetworkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)   

        self.environment_context = environment_context
        self.aws_environment = environment_context["environment_name"]

        self.termination_protection = self.environment_context["stacks-termination-protection"]

        # This creates a VPC with one NAT gateways (N.B. Nat gateways are charged)
        # Nat gateway is necessary for lambda functions to communicates outside the vpc
        # In our case lambdas need to call tenovi and healthie for example
        self.vpc = ec2.Vpc(
            self, "SyntrilloClinicBackendVPC",
            vpc_name = "SyntrilloClinicBackendVPC",
            nat_gateways=1
        )

        # VPC Flow Logs
        if self.aws_environment == "prod":
            self.vpc_flow_logs_log_group = logs.LogGroup(
                self, "VPCFlowLogsLogGroup",
                log_group_name="/aws/vpc/flowlogs",
                removal_policy=RemovalPolicy.DESTROY
            )

            self.vpc.add_flow_log("SyntrilloClinicBackendVPCFlowLogCloudWatch",
                destination=ec2.FlowLogDestination.to_cloud_watch_logs(self.vpc_flow_logs_log_group),
                traffic_type=ec2.FlowLogTrafficType.ALL,
            )

        # Security groups
        self.bastion_host_security_group = ec2.SecurityGroup(
            self,
            "BastionHostSecurityGroup",
            vpc=self.vpc,
        )

        # For VPC Peering with Analytics network
        CfnOutput(self, "SyntrilloClinicNetworkId", value=self.vpc.vpc_id, export_name="SyntrilloClinicNetworkId")

        for subnet in self.vpc.private_subnets:
            CfnOutput(self, f"SyntrilloClinicNetworkRouteTable{subnet.node.id}", value=subnet.route_table.route_table_id, export_name=f"SyntrilloClinicNetworkRouteTable-{subnet.node.id}")
        
        CfnOutput(self, "SyntrilloClinicNetworkCidrBlock", value=self.vpc.vpc_cidr_block, export_name="SyntrilloClinicNetworkCidrBlock")
