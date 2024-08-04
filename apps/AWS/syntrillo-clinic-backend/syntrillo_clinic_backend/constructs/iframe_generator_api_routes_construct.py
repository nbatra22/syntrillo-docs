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
