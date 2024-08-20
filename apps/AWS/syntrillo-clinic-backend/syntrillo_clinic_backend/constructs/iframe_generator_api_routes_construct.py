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

class IFrameGeneratorAPIRoutes(Construct):
    def __init__(self, scope: Construct, id: str, environment_context: dict, api_endpoint: Construct, network: Construct, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.rest_api = api_endpoint.rest_api

    def create_root_resources(self, iframe_generator_function: _lambda.Function):
        self.rest_api.root.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        self.healthie_resource = self.rest_api.root.add_resource("healthie")

        # /iframe_healthie_provider_sidebar
        iframe_healthie_provider_tab = self.rest_api.root.add_resource("iframe_healthie_provider_sidebar")
        iframe_healthie_provider_tab.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab
        iframe_healthie_provider_tab = self.rest_api.root.add_resource("iframe_healthie_provider_tab")
        iframe_healthie_provider_tab.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /download
        download = self.rest_api.root.add_resource("download")
        download_proxy_resource = download.add_resource("{proxy+}")
        download_proxy_resource.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

    def create_static_resources(self, iframe_generator_function: _lambda.Function):
        static = self.rest_api.root.add_resource("static")

        static_proxy_resources = static.add_resource("{proxy+}")
        static_proxy_resources.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

    def create_provider_tab_resources(self, iframe_generator_function: _lambda.Function):

        # ---------------------------------------------------------------------
        # PROVIDER TAB HTML RESOURCES
        # ---------------------------------------------------------------------

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab
        healthie_iframe_provider_tab = self.healthie_resource.add_resource("iframe_provider_tab")

        healthie_iframe_provider_tab_proxy_resources = healthie_iframe_provider_tab.add_resource("{proxy+}")
        healthie_iframe_provider_tab_proxy_resources.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

    def create_provider_sidebar_resources(self, iframe_generator_function: _lambda.Function):
        healthie_iframe_provider_side_bar = self.healthie_resource.add_resource("iframe_provider_sidebar")

        healthie_iframe_provider_side_bar_proxy_resources = healthie_iframe_provider_side_bar.add_resource("{proxy+}")
        healthie_iframe_provider_side_bar_proxy_resources.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )
