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

class IFrameGeneratorApiEndpoint(Construct):
    def __init__(self, scope: Construct, id: str, aws_environment: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.aws_environment = aws_environment
        self.route_53_domain_name = f'{self.aws_environment}.syntrillo-clinic-backend.com'
        self.api_domain_name = f'api.{self.aws_environment}.syntrillo-clinic-backend.com'

        self.route53_hosted_zone_id = ssm.StringParameter.from_string_parameter_attributes(
            self, "SyntrilloClinicRoute53HostedZoneId",
            parameter_name="/syntrillo-clinic/aws/route53/hosted_zone_id"
        ).string_value      

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

        self.rest_api = apigw.RestApi(
            self, "IFramGeneratorAPI",
            rest_api_name="IFramGeneratorAPI",
            domain_name=apigw.DomainNameOptions(
                domain_name=f"api.{aws_environment}.syntrillo-clinic-backend.com",
                certificate=self.certificate
            ),
            deploy_options=apigw.StageOptions(
                tracing_enabled=True,
                stage_name=aws_environment
            )
        )

        # This resource is a minimum for this construct to work on its own
        # this ping resource can also be used for a minimalistic test of the api endpoint
        # jsut to make sure the endpoint is there
        self.rest_api.root.add_resource("ping").add_method(
            "GET",
        ) 

class IFrameGeneratorAPIRoutes(Construct):
    def __init__(self, scope: Construct, id: str, aws_environment: str, api_endpoint: Construct, network: Construct, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.rest_api = api_endpoint.rest_api

    def create_root_resources(self, iframe_generator_function: _lambda.Function):
        self.rest_api.root.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        self.healthie_resource = self.rest_api.root.add_resource("healthie")

        iframe_healthie_provider_tab = self.rest_api.root.add_resource("iframe_healthie_provider_sidebar")
        iframe_healthie_provider_tab.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

    def create_static_resources(self, iframe_generator_function: _lambda.Function):
        static = self.rest_api.root.add_resource("static")

        # /static/healthie/iframe_provider.css
        static_healthie_iframe_provider_css = static.add_resource("healthie").add_resource("iframe_provider.css")
        static_healthie_iframe_provider_css.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

    def create_provider_tab_resources(self, iframe_generator_function: _lambda.Function):

        # ---------------------------------------------------------------------
        # PROVIDER TAB HTML RESOURCES
        # ---------------------------------------------------------------------

        # /iframe_healthie_provider_tab
        iframe_healthie_provider_tab = self.rest_api.root.add_resource("iframe_healthie_provider_tab")
        iframe_healthie_provider_tab.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab
        healthie_iframe_provider_tab = self.healthie_resource.add_resource("iframe_provider_tab")

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/status
        healthie_iframe_provider_tab_status = healthie_iframe_provider_tab.add_resource("status")
        healthie_iframe_provider_tab_status.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/devices
        healthie_iframe_provider_tab_devices = healthie_iframe_provider_tab.add_resource("devices")
        healthie_iframe_provider_tab_devices.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/onboarding
        healthie_iframe_provider_tab_care_plan = healthie_iframe_provider_tab.add_resource("onboarding")
        healthie_iframe_provider_tab_care_plan.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/care_plan
        healthie_iframe_provider_tab_care_plan = healthie_iframe_provider_tab.add_resource("care_plan")
        healthie_iframe_provider_tab_care_plan.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/cdss
        healthie_iframe_provider_tab_cdss = healthie_iframe_provider_tab.add_resource("cdss")
        healthie_iframe_provider_tab_cdss.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/system
        healthie_iframe_provider_tab_system = healthie_iframe_provider_tab.add_resource("system")
        healthie_iframe_provider_tab_system.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/system_devices
        healthie_iframe_provider_tab_system_devices = healthie_iframe_provider_tab.add_resource("system_devices")
        healthie_iframe_provider_tab_system_devices.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # ---------------------------------------------------------------------
        # PROVIDER TAB DATA RESOURCES
        # ---------------------------------------------------------------------

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/devices/tenovi_generate_temporary_pairing_code_form
        healthie_iframe_provider_tab_system_devices_sync_measurements_form = healthie_iframe_provider_tab_system_devices.add_resource("sync_measurements_form")
        healthie_iframe_provider_tab_system_devices_sync_measurements_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/devices/tenovi_generate_temporary_pairing_code_form
        healthie_iframe_provider_tab_system_devices_tenovi_generate_temporary_pairing_code_form = healthie_iframe_provider_tab_system_devices.add_resource("tenovi_generate_temporary_pairing_code_form")
        healthie_iframe_provider_tab_system_devices_tenovi_generate_temporary_pairing_code_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/devices/tenovi_pair_devices_form
        healthie_iframe_provider_tab_system_devices_tenovi_pair_devices_form = healthie_iframe_provider_tab_system_devices.add_resource("tenovi_pair_devices_form")
        healthie_iframe_provider_tab_system_devices_tenovi_pair_devices_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        ) 

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/system/register_patient_at_syntrillo_form
        healthie_iframe_provider_tab_system_register_patient_at_syntrillo_form = healthie_iframe_provider_tab_system.add_resource("register_patient_at_syntrillo_form")
        healthie_iframe_provider_tab_system_register_patient_at_syntrillo_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab/system_devices/tenovi_dummy_data_generator_form
        healthie_iframe_provider_tab_system_devices_tenovi_dummy_data_generator_form = healthie_iframe_provider_tab_system_devices.add_resource("tenovi_dummy_data_generator_form")
        healthie_iframe_provider_tab_system_devices_tenovi_dummy_data_generator_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /healthie/iframe_provider_tab/devices/tenovi_order_new_devices_form
        healthie_iframe_provider_tab_devices_tenovi_order_new_devices_form= healthie_iframe_provider_tab_devices.add_resource("tenovi_order_new_devices_form")
        healthie_iframe_provider_tab_devices_tenovi_order_new_devices_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /healthie/iframe_provider_tab/care_plan/get_blood_pressure_plot
        healthie_iframe_provider_tab_care_plan_get_blood_pressure_plot = healthie_iframe_provider_tab_care_plan.add_resource("get_blood_pressure_plot")
        healthie_iframe_provider_tab_care_plan_get_blood_pressure_plot.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /healthie/iframe_provider_tab/care_plan/get_pulse_plot
        healthie_iframe_provider_tab_care_plan_get_pulse_plot = healthie_iframe_provider_tab_care_plan.add_resource("get_pulse_plot")
        healthie_iframe_provider_tab_care_plan_get_pulse_plot.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /healthie/iframe_provider_tab/care_plan/get_heart_rate_statistics_plot
        healthie_iframe_provider_tab_care_plan_get_heart_rate_statistics_plot = healthie_iframe_provider_tab_care_plan.add_resource("get_heart_rate_statistics_plot")
        healthie_iframe_provider_tab_care_plan_get_heart_rate_statistics_plot.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

    def create_provider_sidebar_resources(self, iframe_generator_function: _lambda.Function):
        provider_sidebar_resource = self.healthie_resource.add_resource("iframe_provider_sidebar")

        # provider_sidebar_resource.add_resource("status").add_method(
        #     "POST", apigw.LambdaIntegration(iframe_generator_function)
        # )
        # provider_sidebar_resource.add_resource("system").add_method(
        #     "POST", apigw.LambdaIntegration(iframe_generator_function)
        # )
        # provider_sidebar_resource.add_resource("questionnaire").add_method(
        #     "POST", apigw.LambdaIntegration(iframe_generator_function)
        # )

class IFrameGeneratorFunction(Construct):
    def __init__(self, scope: Construct, id: str,
                 environment_context: dict,
                 network: Construct, 
                 database: Construct,
                 storage: Construct,
                 secrets: Construct,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        self.environment_context = environment_context
        self.network = network
        self.database = database
        self.storage = storage
        self.secrets = secrets

        params_and_secrets = _lambda.ParamsAndSecretsLayerVersion.from_version(_lambda.ParamsAndSecretsVersions.V1_0_103,
            cache_size=500,
            log_level=_lambda.ParamsAndSecretsLogLevel.DEBUG
        )

        self.function = _lambda.Function(self, "IFrameGeneratorFunction",
            function_name="IFrameGeneratorFunction",
            vpc = self.network.vpc,
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda-functions/iframe-generator-function", exclude=['.env']),
            params_and_secrets=params_and_secrets,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.storage.efs_access_point,
                "/mnt/python_modules"
            ),
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "PYTHONPATH": "/mnt/python_modules",
                "AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN": self.database.secret.secret_arn,
                "AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN": self.secrets.tenovi_hwi_secrets.secret_arn,
                "AWS_SECRETS_MANAGER_HEALTHIE_SECRET_ARN": self.secrets.healthie_secrets.secret_arn
            },
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=512,
            timeout=Duration.seconds(60),
        )

        self.function_version = _lambda.Version(
            self, "LambdaVersion",
            lambda_=self.function,
        )

        self.function_alias = _lambda.Alias(
            self, "LambdaAlias",
            alias_name="provisionned-concurrency",
            version=self.function_version,
            provisioned_concurrent_executions=self.environment_context['iframe_generator_function']['provisioned_concurrency_executions']
        )

        self.database.secret.grant_read(self.function)
        self.secrets.tenovi_hwi_secrets.grant_read(self.function)
        self.secrets.healthie_secrets.grant_read(self.function)

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class ServersStack(Stack):
        
    def __init__(self, scope: Construct, id: str, 
            aws_environment,
            environment_context,
            network,
            database,
            storage,
            secrets,
            **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        self.aws_environment = aws_environment
        self.environment_context = environment_context
        self.network = network
        self.database = database
        self.storage = storage
        self.secrets = secrets

        self.iframe_generator_function = IFrameGeneratorFunction(
            self, "IFrameGeneratorFunction",
            environment_context=self.environment_context,
            network=self.network,
            database=self.database,
            storage=self.storage,
            secrets=self.secrets
        )

        self.iframe_generator_api_endpoint = IFrameGeneratorApiEndpoint(
            self, "IFrameGeneratorApiEndpoint",
            aws_environment=self.aws_environment
        )

        self.iframe_generator_api_routes = IFrameGeneratorAPIRoutes(
            self, "IFrameGeneratorApiRoutes",
            aws_environment=self.aws_environment,
            api_endpoint=self.iframe_generator_api_endpoint,
            network=self.network
        )

        self.iframe_generator_api_routes.create_root_resources(self.iframe_generator_function.function_alias)
        self.iframe_generator_api_routes.create_static_resources(self.iframe_generator_function.function_alias)
        self.iframe_generator_api_routes.create_provider_tab_resources(self.iframe_generator_function.function_alias)
        self.iframe_generator_api_routes.create_provider_sidebar_resources(self.iframe_generator_function.function_alias)

        # ---------------------------------------------------------------------
        # API RESOURCES & METHODES (END)
        # ---------------------------------------------------------------------

        # route53.ARecord(self, "SyntrilloCustomDomainARecord", 
        #     zone=hosted_zone,
        #     record_name=f"api.{self.aws_environment}.syntrillo-clinic-backend.com",
        #     target=route53.RecordTarget.from_alias(
        #         route53_targets.ApiGateway(iframe_generator_api.rest_api)
        #     )
        # )