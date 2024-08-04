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
            zone_name=f"{self.environment_name}.{self.route53_hosted_zone_id}",
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

        self.rest_api = apigw.RestApi(
            self, "IFramGeneratorAPI",
            rest_api_name="IFramGeneratorAPI",
            domain_name=apigw.DomainNameOptions(
                domain_name=f"api.{self.environment_name}.syntrillo-clinic-backend.com",
                certificate=self.certificate
            ),
            deploy_options=apigw.StageOptions(
                tracing_enabled=True,
                stage_name=self.environment_name
            )
        )

        # This resource is a minimum for this construct to work on its own
        # this ping resource can also be used for a minimalistic test of the api endpoint
        # jsut to make sure the endpoint is there
        self.rest_api.root.add_resource("ping").add_method(
            "GET",
        ) 