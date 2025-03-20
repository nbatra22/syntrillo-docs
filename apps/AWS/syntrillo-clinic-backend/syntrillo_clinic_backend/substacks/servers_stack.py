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
# CONSTRUCTS
# -----------------------------------------------------------------------------

from syntrillo_clinic_backend.constructs.iframe_generator_api_endpoint_construct import IFrameGeneratorApiEndpoint
from syntrillo_clinic_backend.constructs.iframe_generator_api_routes_construct import IFrameGeneratorAPIRoutes

from syntrillo_clinic_backend.constructs.servers.iframe_generator_function_construct import IFrameGeneratorFunction
from syntrillo_clinic_backend.constructs.servers.message_endpoint_function_construct import MessageEndpointFunction
from syntrillo_clinic_backend.constructs.servers.blood_pressure_notification_function_construct import BloodPressureNotificationFunction
from syntrillo_clinic_backend.constructs.servers.llm_server_construct import LLMServer

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class ServersStack(Stack):
        
    def __init__(self, scope: Construct, id: str,
            environment_context,
            network,
            database,
            storage,
            secrets,
            **kwargs) -> None:
        super().__init__(scope, id, **kwargs)


        self.environment_context = environment_context
        self.network = network
        self.database = database
        self.storage = storage
        self.secrets = secrets
        
        self.termination_protection = self.environment_context["stacks-termination-protection"]

        self.iframe_generator_function = IFrameGeneratorFunction(
            self, "IFrameGeneratorFunction",
            environment_context=self.environment_context,
            network=self.network,
            database=self.database,
            storage=self.storage, 
            secrets=self.secrets,
        )

        self.message_endpoint_function = MessageEndpointFunction(
            self, "MessageEndpointFunction",
            environment_context=self.environment_context,
            network=self.network,
            database=self.database,
            storage=self.storage, 
            secrets=self.secrets,
        )

        self.llm_server = LLMServer(
            self, "LLMServer",
            environment_context=self.environment_context,
            network=self.network,
            database=self.database,
            iframe_generator_function=self.iframe_generator_function,
        )

        self.iframe_generator_api_endpoint = IFrameGeneratorApiEndpoint(
            self, "IFrameGeneratorApiEndpoint",
            environment_context=self.environment_context
        )

        self.iframe_generator_api_routes = IFrameGeneratorAPIRoutes(
            self, "IFrameGeneratorApiRoutes",
            environment_context=self.environment_context,
            api_endpoint=self.iframe_generator_api_endpoint,
            network=self.network
        )

        self.iframe_generator_api_routes.create_root_resources(self.iframe_generator_function.function_alias)
        self.iframe_generator_api_routes.create_healthie_endpoint(self.message_endpoint_function.function_alias)
        self.iframe_generator_api_routes.create_static_resources(self.iframe_generator_function.function_alias)
        self.iframe_generator_api_routes.create_provider_tab_resources(self.iframe_generator_function.function_alias)
        self.iframe_generator_api_routes.create_provider_sidebar_resources(self.iframe_generator_function.function_alias)


        if self.environment_context["environment_name"] == "staging":
            self.blood_pressure_notification_function = BloodPressureNotificationFunction(
                self, "BloodPressureNotificationFunction",
                environment_context=self.environment_context,
                network=self.network,
                database=self.database,
                storage=self.storage, 
                secrets=self.secrets,
            )

            self.iframe_generator_api_routes.create_tenovi_endpoint(self.blood_pressure_notification_function.function_alias)