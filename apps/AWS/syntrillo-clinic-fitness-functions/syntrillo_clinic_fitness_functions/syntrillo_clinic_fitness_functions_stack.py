from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_certificatemanager as acm,
)
from constructs import Construct

class SyntrilloClinicFitnessFunctionsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(self, "SyntrilloClinicBackendHostedZone",
            zone_name="prod.syntrillo-clinic-backend.com",
            hosted_zone_id="Z007344818F52SMLDPLCV"
        )
        self.hosted_zone = hosted_zone

        certificate = acm.Certificate( self, "SyntrilloClinicBackendSSLCertificate",
            domain_name="prod.syntrillo-clinic-backend.com",
            validation=acm.CertificateValidation.from_dns(self.hosted_zone),
            subject_alternative_names=[
                "api.prod.syntrillo-clinic-backend.com"
            ]
        )
        self.certificate = certificate

        fitness_function=_lambda.Function(
            self, "FitnessFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda-functions/fitness-function"),
        )

        fitness_api=apigw.LambdaRestApi(
            self, "FitnessAPI",
            handler=fitness_function,
            proxy=False,
            domain_name=apigw.DomainNameOptions(
                domain_name="api.prod.syntrillo-clinic-backend.com",
                certificate=self.certificate
            ),
            deploy_options= apigw.StageOptions(
                tracing_enabled=True,
                stage_name="prod"
            )
        )


        root_resource = fitness_api.root
        
        iframe_healthie_provider_tab = root_resource.add_resource("iframe_healthie_provider_tab")
        iframe_healthie_provider_tab.add_method(
            "GET",
            apigw.LambdaIntegration(fitness_function),
        ) 

        iframe_healthie_provider_tab = root_resource.add_resource("iframe_healthie_client_sidebar")
        iframe_healthie_provider_tab.add_method(
            "GET",
            apigw.LambdaIntegration(fitness_function),
        )       
                
        iframe_healthie_provider_tab = root_resource.add_resource("iframe_healthie_provider_sidebar")
        iframe_healthie_provider_tab.add_method(
            "GET",
            apigw.LambdaIntegration(fitness_function),
        )       

        route53.ARecord(self, "SyntrilloCustomDomainARecord", 
            zone=hosted_zone,
            record_name="api.prod.syntrillo-clinic-backend.com",
            target=route53.RecordTarget.from_alias(
                route53_targets.ApiGateway(fitness_api)
            )
        )
        