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
    
class NetworkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, aws_environment, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # parameters
        self.aws_environment = aws_environment
        self.route_53_domain_name = f'{self.aws_environment}.syntrillo-clinic-backend.com'
        self.api_domain_name = f'api.{self.aws_environment}.syntrillo-clinic-backend.com'

        self.route53_hosted_zone_id = ssm.StringParameter.from_string_parameter_attributes(
            self, "SyntrilloClinicRoute53HostedZoneId",
            parameter_name="/syntrillo-clinic/aws/route53/hosted_zone_id"
        ).string_value        

        # This creates a VPC with one NAT gateways (N.B. Nat gateways are charged)
        # Nat gateway is necessary for lambda functions to communicates outside the vpc
        # In our case lambdas need to call tenovi and healthie for example
        self.vpc = ec2.Vpc(
            self, "SyntrilloClinicBackendVPC",
            vpc_name = "SyntrilloClinicBackendVPC",
            nat_gateways=1
        )

        self.hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "SyntrilloClinicBackendHostedZone",
            zone_name=f"{self.aws_environment}.{self.route53_hosted_zone_id}",
            hosted_zone_id=self.route53_hosted_zone_id
        )

        self.certificate = acm.Certificate(
            self, "SyntrilloClinicBackendSSLCertificate",
            domain_name=self.route_53_domain_name,
            validation=acm.CertificateValidation.from_dns(self.hosted_zone),
            subject_alternative_names=[
                self.api_domain_name
            ]
        )