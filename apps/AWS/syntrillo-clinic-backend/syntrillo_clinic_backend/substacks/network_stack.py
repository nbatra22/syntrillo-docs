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
# CONSTRUCTS
# -----------------------------------------------------------------------------

class SyntrilloClinicBastionStack(Construct):
    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, network: Construct, database: Construct, storage: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.network = network
        self.database = database
        self.storage = storage

        self.vpc = ec2.Vpc.from_vpc_attributes(self, "ImportedVpc",
            vpc_id=Fn.import_value("SyntrilloClinic-Network-Vpc-Id"),
            availability_zones=[Fn.import_value("SyntrilloClinic-Network-Vpc-AvailabilityZone-0"), Fn.import_value("SyntrilloClinic-Network-Vpc-AvailabilityZone-1")],
            private_subnet_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet1-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet2-Id")],
            public_subnet_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet1-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet2-Id")],
            private_subnet_route_table_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet1-RouteTable-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PrivateSubnet2-RouteTable-Id")],
            public_subnet_route_table_ids=[Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet1-RouteTable-Id"), Fn.import_value("SyntrilloClinic-Network-Vpc-PublicSubnet2-RouteTable-Id")]
        )

        # Bastion security group is always created (can be used by ClouShell VPC)
        self.bastion_host_security_group = ec2.SecurityGroup(
            self,
            "BastionHostSecurityGroup",
            vpc=self.vpc,
        )

        if self.environment_context["bastion"]["bastion-enabled"]:

            bation_host_instance_size = self.environment_context["bastion"]["bastion-instance-size"]

            # Create the bastion host
            bastion_host = ec2.BastionHostLinux(
                self, "BastionHost",
                vpc=self.vpc,
                instance_type=ec2.InstanceType(bation_host_instance_size),
                subnet_selection=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PUBLIC,
                ),
                security_group=self.bastion_host_security_group,
                machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            )

            # Mount efs file system on the bastion host
            # efs_file_system_id = self.storage.efs_file_system.file_system_id

            clinic_storage_efs_file_system_id = Fn.import_value("SyntrilloClinic-Storage-EFS-FileSystem-Id")

            user_data = ec2.UserData.for_linux()
            user_data.add_commands(
                "set -xe",
                "cd /home/ec2-user", 
                "mkdir -p efs",
                f"sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport {clinic_storage_efs_file_system_id}.efs.us-east-1.amazonaws.com:/ efs",
                "chown ec2-user:ec2-user efs",
                "yum install -y -q mariadb105",
                "yum install -y -q docker",
                "systemctl start docker",
                "chmod 666 /var/run/docker.sock",
                "usermod -a -G docker ec2-user",
            )
            bastion_host.instance.add_user_data(user_data.render())

        # ---------------------------------------------------------------------
        # OUTPUTS
        # ---------------------------------------------------------------------

        CfnOutput(self, "SyntrilloClinicBastionSecurityGroupId",
            value=self.bastion_host_security_group.security_group_id,
            export_name="SyntrilloClinic-Bastion-SecurityGroup-Id-2"
        )


# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------
    
class NetworkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)   

        # ---------------------------------------------------------------------
        # INPUTS
        # ---------------------------------------------------------------------
        self.environment_context = environment_context
        self.aws_environment = environment_context["environment_name"]

        self.termination_protection = self.environment_context["stacks-termination-protection"]

        # ---------------------------------------------------------------------
        # Create VPC
        # ---------------------------------------------------------------------
        # This creates a VPC with one NAT gateways (N.B. Nat gateways are charged)
        # Nat gateway is necessary for lambda functions to communicates outside the vpc
        # In our case lambdas need to call tenovi and healthie for example
        self.vpc = ec2.Vpc(
            self, "SyntrilloClinicBackendVPC",
            vpc_name = "SyntrilloClinicBackendVPC",
            nat_gateways=1
        )

        # ---------------------------------------------------------------------
        # Enable VPC Flow Logs
        # ---------------------------------------------------------------------
        self.vpc_flow_logs_log_group = logs.LogGroup(
            self, "VPCFlowLogsLogGroup",
            log_group_name="/aws/vpc/flowlogs",
            removal_policy=RemovalPolicy.DESTROY
        )

        self.vpc.add_flow_log("SyntrilloClinicBackendVPCFlowLogCloudWatch",
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(self.vpc_flow_logs_log_group),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

        # ---------------------------------------------------------------------
        # Create Bastion host security group (To delete)
        # ---------------------------------------------------------------------
        self.bastion_host_security_group = ec2.SecurityGroup(
            self,
            "BastionHostSecurityGroup",
            vpc=self.vpc,
        )

        # ---------------------------------------------------------------------
        # Add S3 Gateway Endpoint
        # ---------------------------------------------------------------------
        self.vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3
        )

        # ---------------------------------------------------------------------
        # Add Bedrock Interface Endpoint
        # ---------------------------------------------------------------------
        security_group = ec2.SecurityGroup(
            self, "BedrockEndpointSG",
            vpc=self.vpc,
            description="Security Group for Bedrock VPC Endpoint",
            allow_all_outbound=True
        )

        security_group.add_ingress_rule(
            ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            ec2.Port.tcp(443),
            "Allow HTTPS inbound from VPC"
        )

        bedrock_endpoint = ec2.InterfaceVpcEndpoint(
            self, "BedrockVPCEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointService("com.amazonaws.us-east-1.bedrock-runtime"),
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[security_group]
        )

        # ---------------------------------------------------------------------
        # OUTPUTS
        # ---------------------------------------------------------------------
        CfnOutput(self, "SyntrilloClinicNetworkVpcId", value=self.vpc.vpc_id, export_name="SyntrilloClinic-Network-Vpc-Id")
        CfnOutput(self, "SyntrilloClinicNetworkVpcCidrBlock", value=self.vpc.vpc_cidr_block, export_name="SyntrilloClinic-Network-Vpc-CidrBlock")

        # Output route table ID and subnet ID for each private subnet
        for subnet in self.vpc.private_subnets:
            CfnOutput(self, f"SyntrilloClinicNetworkVpc{subnet.node.id}RouteTableId", value=subnet.route_table.route_table_id, export_name=f"SyntrilloClinic-Network-Vpc-{subnet.node.id}-RouteTable-Id")
            CfnOutput(self, f"SyntrilloClinicNetworkVpc{subnet.node.id}SubnetId", value=subnet.subnet_id, export_name=f"SyntrilloClinic-Network-Vpc-{subnet.node.id}-Id")
            
        # Output route table ID and subnet ID for each public subnet    
        for subnet in self.vpc.public_subnets:
            CfnOutput(self, f"SyntrilloClinicNetworkVpc{subnet.node.id}RouteTableId", value=subnet.route_table.route_table_id, export_name=f"SyntrilloClinic-Network-Vpc-{subnet.node.id}-RouteTable-Id")
            CfnOutput(self, f"SyntrilloClinicNetworkVpc{subnet.node.id}SubnetId", value=subnet.subnet_id, export_name=f"SyntrilloClinic-Network-Vpc-{subnet.node.id}-Id")    
        
        # output availability zones
        for i, az in enumerate(self.vpc.availability_zones):
            CfnOutput(self, f"SyntrilloClinicNetworkVpcAvailabilityZone{i}", value=az, export_name=f"SyntrilloClinic-Network-Vpc-AvailabilityZone-{i}")
