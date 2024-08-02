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
import boto3

class ServersStack(Stack):

    def get_latest_layer_version_arn(self, layer_name: str) -> str:
        lambda_client = boto3.client('lambda')
        response = lambda_client.list_layer_versions(LayerName=layer_name)
        
        if not response['LayerVersions']:
            raise ValueError(f"No versions found for layer: {layer_name}")
        
        # The versions are returned in descending order, so the first one is the latest
        latest_version = response['LayerVersions'][0]
        return latest_version['LayerVersionArn'] 
        
    def __init__(self, scope: Construct, id: str, 
            aws_environment,
            vpc,
            database,
            hosted_zone, 
            certificate, 
            file_system, 
            access_point,
            secrets,
            api_domain_name,
            **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        self.aws_environment = aws_environment
        self.vpc = vpc
        self.database = database
        self.hosted_zone = hosted_zone
        self.certificate = certificate
        self.access_point = access_point
        self.file_system = file_system
        self.secrets = secrets
        self.api_domain_name = api_domain_name

        params_and_secrets = _lambda.ParamsAndSecretsLayerVersion.from_version(_lambda.ParamsAndSecretsVersions.V1_0_103,
            cache_size=500,
            log_level=_lambda.ParamsAndSecretsLogLevel.DEBUG
        )

        iframe_generator_function = _lambda.Function(self, "IFrameGeneratorFunction",
            function_name="IFrameGeneratorFunction",
            vpc = self.vpc,
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda-functions/iframe-generator-function", exclude=['.env']),
            params_and_secrets=params_and_secrets,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.access_point,
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

        self.database.secret.grant_read(iframe_generator_function)
        self.secrets.tenovi_hwi_secrets.grant_read(iframe_generator_function)
        self.secrets.healthie_secrets.grant_read(iframe_generator_function)

        iframe_generator_api = apigw.RestApi(self, "IFramGeneratorAPI", 
            rest_api_name="IFramGeneratorAPI",
            domain_name=apigw.DomainNameOptions(
                domain_name="api.prod.syntrillo-clinic-backend.com",
                certificate=self.certificate
            ),
            deploy_options= apigw.StageOptions(
                tracing_enabled=True,
                stage_name="prod"
            )
        )

        # ---------------------------------------------------------------------
        # API RESOURCES & METHODES (START)
        # ---------------------------------------------------------------------
        root_resource = iframe_generator_api.root

        root_method = root_resource.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /static
        static = root_resource.add_resource("static")

        # /static/healthie/iframe_provider.css
        static_healthie_iframe_provider_css = static.add_resource("healthie").add_resource("iframe_provider.css")
        static_healthie_iframe_provider_css.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )
        
        # /healthie
        healthie = root_resource.add_resource("healthie")

        # -------------------
        # IFRAMES / HTML PAGE (PROVIDER_SIDEBAR)
        # -------------------

        # /iframe_healthie_provider_tab
        iframe_healthie_provider_tab = root_resource.add_resource("iframe_healthie_provider_sidebar")
        iframe_healthie_provider_tab.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /healthie/iframe_provider_sidebar
        healthie_iframe_provider_sidebar = healthie.add_resource("iframe_provider_sidebar")

        # /healthie/iframe_provider_sidebar/status
        iframe_healthie_provider_tab = healthie_iframe_provider_sidebar.add_resource("status")
        iframe_healthie_provider_tab.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /healthie/iframe_provider_sidebar/system
        iframe_healthie_provider_tab = healthie_iframe_provider_sidebar.add_resource("system")
        iframe_healthie_provider_tab.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /healthie/iframe_provider_sidebar/questionnaire
        iframe_healthie_provider_tab = healthie_iframe_provider_sidebar.add_resource("questionnaire")
        iframe_healthie_provider_tab.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # -------------------
        # IFRAMES / HTML PAGE (PROVIDER_TAB)
        # -------------------

        # /iframe_healthie_provider_tab
        iframe_healthie_provider_tab = root_resource.add_resource("iframe_healthie_provider_tab")
        iframe_healthie_provider_tab.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab
        healthie_iframe_provider_tab = healthie.add_resource("iframe_provider_tab")

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

        # -------------------
        # IFRAMES / DATA API
        # -------------------

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

        # ---------------------------------------------------------------------
        # API RESOURCES & METHODES (END)
        # ---------------------------------------------------------------------

        # route53.ARecord(self, "SyntrilloCustomDomainARecord", 
        #     zone=hosted_zone,
        #     record_name="api.prod.syntrillo-clinic-backend.com",
        #     target=route53.RecordTarget.from_alias(
        #         route53_targets.ApiGateway(iframe_generator_api)
        #     )
        # )
