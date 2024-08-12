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

class IFrameGeneratorApiEndpoint(Construct):
    def __init__(self, scope: Construct, id: str, environment_context: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.environment_context = environment_context
        self.environment_name = self.environment_context["environment_name"]

        self.route_53_domain_name = f'{self.environment_name}.syntrillo-clinic-backend.com'
        self.api_domain_name = f'api.{self.environment_name}.syntrillo-clinic-backend.com'

        self.route53_hosted_zone_id = ssm.StringParameter.from_string_parameter_attributes(
            self, "SyntrilloClinicRoute53HostedZoneId",
            parameter_name="/syntrillo-clinic/aws/route53/hosted_zone_id"
        ).string_value      

        self.hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "SyntrilloClinicBackendHostedZone",
            zone_name=f"{self.environment_name}.syntrillo-clinic-backend.com",
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

        # Add IP restrictions to the API endpoint
        allowed_ip_addresses = []
        for ip_info in self.environment_context["iframe_generator_api"]["allowed_api_adresses"]:
            allowed_ip_addresses.append(ip_info["ip"])

        # Create the IAM policy statement
        allow_all_invokes_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.DENY,
            principals=[iam.AnyPrincipal()],
            actions=["execute-api:Invoke"],
            resources=[f"execute-api:/*/*/*"],
            conditions={
                "NotIpAddress": {
                    "aws:SourceIp": allowed_ip_addresses,
                }
            },
        )

        allowed_ips_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            principals=[iam.AnyPrincipal()],
            actions=["execute-api:Invoke"],
            resources=[f"execute-api:/*/*/*"]
        )

        # Create rest api
        self.rest_api = apigw.RestApi(
            self, "IFramGeneratorAPI",
            rest_api_name="IFramGeneratorAPI",
            domain_name=apigw.DomainNameOptions(
                domain_name=f"api.{self.environment_name}.syntrillo-clinic-backend.com",
                certificate=self.certificate
            ),
            deploy_options=apigw.StageOptions(
                tracing_enabled=True,
                stage_name=self.environment_name,
                throttling_rate_limit=1000,
                throttling_burst_limit=500
            ),
            policy=iam.PolicyDocument(statements=[
                allow_all_invokes_policy_statement, 
                allowed_ips_policy_statement
            ])
        )

        route53.ARecord(self, "SyntrilloCustomDomainARecord", 
            zone=self.hosted_zone,
            record_name=f"api.{self.environment_name}.syntrillo-clinic-backend.com",
            target=route53.RecordTarget.from_alias(
                route53_targets.ApiGateway(self.rest_api)
            )
        )

        # This resource is a minimum for this construct to work on its own
        # this ping resource can also be used for a minimalistic test of the api endpoint
        # jsut to make sure the endpoint is there
        self.rest_api.root.add_resource("ping").add_method(
            "GET",
        )

