from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    Fn,
    aws_ec2 as ec2,
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
        self.aws_environment = environment_context["environment-name"]

        # self.termination_protection = self.environment_context["stacks-termination-protection"]

        # This creates a VPC with no NAT gateways (N.B. Nat gateways are charged)
        # We do not need to access the public internet for analytics
        self.vpc = ec2.Vpc(
            self, "SyntrilloAnalyticsBackendVPC", 
            vpc_name = "SyntrilloAnalyticsBackendVPC",
            nat_gateways=0,
            ip_addresses=ec2.IpAddresses.cidr("10.1.0.0/16"),            
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ],
        )

        # VPC Flow Logs
        self.vpc_flow_logs_log_group = logs.LogGroup(
            self, "VPCFlowLogsLogGroup",
            log_group_name="/aws/vpc/flowlogs/syntrillo-analytics",
            removal_policy=RemovalPolicy.DESTROY
        )

        self.vpc.add_flow_log("SyntrilloAnalyticsBackendVPCFlowLogCloudWatch",
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(self.vpc_flow_logs_log_group),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

        self.dms_security_group = ec2.SecurityGroup(
            self, "DMSSecurityGroup",
            vpc=self.vpc,
            description="Security group for DMS",
            allow_all_outbound=True
        )

        # Add S3 Gateway Endpoint
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )

        # Create VPC Endpoint for Secrets Manager
        self.vpc.add_interface_endpoint(
            "SecretsManagerEndpoint",
            service=ec2.InterfaceVpcEndpointService(
                name="com.amazonaws.{}.secretsmanager".format(self.region)
            ),
            private_dns_enabled=True,
            # # Optional: You can specify which subnets to place the endpoint in
            # subnets=ec2.SubnetSelection(
            #     subnet_type=ec2.SubnetType.ISOLATED
            # ),
            # # Optional: Control access to the endpoint with a security group
            # security_groups=[ec2.SecurityGroup(
            #     self, 
            #     "SecretsManagerEndpointSG",
            #     vpc=vpc,
            #     description="Security group for Secrets Manager VPC Endpoint"
            # )]
        )

        syntrillo_clinic_network_id = Fn.import_value("SyntrilloClinicNetworkId")

        # Create VPC Peering Connection
        peering_connection = ec2.CfnVPCPeeringConnection(
            self, "SyntrillloAnalyticsToSyntrilloClinicVPCPeering",
            vpc_id=self.vpc.vpc_id,
            peer_vpc_id=syntrillo_clinic_network_id
        )


        # Update SyntrilloClinic subnet route tables, with SyntrilloAnalytics vpc cidrblock
        private_subnet_1_route_table = Fn.import_value("SyntrilloClinicNetworkRouteTable-PrivateSubnet1")
        private_subnet_2_route_table = Fn.import_value("SyntrilloClinicNetworkRouteTable-PrivateSubnet2")

        private_sunet_1_route = ec2.CfnRoute(
            self,
            f"RouteFromSyntriloClinicVpcToSyntilloAnalyticsVpc1",
            route_table_id=private_subnet_1_route_table,
            destination_cidr_block=self.vpc.vpc_cidr_block,
            vpc_peering_connection_id=peering_connection.ref
        )

        private_sunet_2_route = ec2.CfnRoute(
            self,
            f"RouteFromSyntriloClinicVpcToSyntilloAnalyticsVpc2",
            route_table_id=private_subnet_2_route_table,
            destination_cidr_block=self.vpc.vpc_cidr_block,
            vpc_peering_connection_id=peering_connection.ref
        )

        # Update SyntrilloAnalytics subnet route tables, with SyntrilloClinic vpc cidrblock
        syntrillo_clinic_cidr_block = Fn.import_value("SyntrilloClinicNetworkCidrBlock")
        for subnet in self.vpc.isolated_subnets:
            ec2.CfnRoute(
                self,
                f"RouteFromSyntriloAnalyticsVpcToSyntilloClinicVpc{subnet.node.id}",
                route_table_id=subnet.route_table.route_table_id,
                destination_cidr_block=syntrillo_clinic_cidr_block,
                vpc_peering_connection_id=peering_connection.ref
            )

        # Output the list of the isolated subnets ids as a list
        CfnOutput(self, "SyntrilloAnalyticsNetworkIsolatedSubnetId1", value=self.vpc.isolated_subnets[0].subnet_id, export_name="SyntrilloAnalyticsNetworkIsolatedSubnetId-1")
        CfnOutput(self, "SyntrilloAnalyticsNetworkIsolatedSubnetId2", value=self.vpc.isolated_subnets[1].subnet_id, export_name="SyntrilloAnalyticsNetworkIsolatedSubnetId-2")
        # # Output bastion security group id
        CfnOutput(self, "SyntrilloAnalyticsBastionHostSecurityGroupId", value=self.dms_security_group.security_group_id, export_name="SyntrilloAnalyticsNetworkDMSSecurityGroupId")