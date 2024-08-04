from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_ssm as ssm
)
from constructs import Construct

class SimpleCdkProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create a lambda function with python 3.9 runtime
        lambda_function = _lambda.Function(
            self,
            "SimpleLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda"),
            handler="lambda_function.lambda_handler",
        )

        self.environment_name = 'sandbox'
        self.route_53_domain_name = f'{self.environment_name}.syntrillo-clinic-backend.com'
        self.api_domain_name = f'api-2.{self.environment_name}.syntrillo-clinic-backend.com'

        self.route53_hosted_zone_id = ssm.StringParameter.from_string_parameter_attributes(
            self, "HostedZoneId",
            parameter_name="/syntrillo-clinic/aws/route53/hosted_zone_id"
        ).string_value      

        self.hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "HostedZone",
            zone_name=f"{self.route_53_domain_name}",
            hosted_zone_id=self.route53_hosted_zone_id
        )

        # create a new certificate with aws acm
        self.certificate = acm.Certificate(
            self, "Certificate",
            domain_name=self.route_53_domain_name,
            validation=acm.CertificateValidation.from_dns(self.hosted_zone),
            subject_alternative_names=[
                self.api_domain_name
            ]
        )

        # Create an API Gateway REST API
        self.api = apigateway.RestApi(
            self,
            "SimpleApiGateway",
            rest_api_name="Simple API",
            deploy_options=apigateway.StageOptions(stage_name="prod"),
            domain_name=apigateway.DomainNameOptions(
                domain_name=f"{self.api_domain_name}",
                certificate=self.certificate
            ),
        )

        route53.ARecord(self, "ARecord", 
            zone=self.hosted_zone,
            record_name=f"{self.api_domain_name}",
            target=route53.RecordTarget.from_alias(
                route53_targets.ApiGateway(self.api)
            )
        )

        # add get method to the root resource of the api gateway
        self.api.root.add_method("GET", integration=apigateway.LambdaIntegration(lambda_function))
