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
)
from constructs import Construct

# -----------------------------------------------------------------------------
# CONSTRUCTS
# -----------------------------------------------------------------------------

import boto3

class CheckBehaviourConstruct(Construct):

    def __init__(self, scope: Construct, id: str, vpc, efs_access_point, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = vpc
        self.efs_access_point = efs_access_point

        check_behaviour_function = _lambda.Function(
            self, "CheckBehaviourFunction",
            function_name="CheckBehaviourFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="check_behaviour_function.handler",
            code=_lambda.Code.from_asset("lambda-functions/fitness-functions/check-behaviour-function"),
            vpc = self.vpc,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.efs_access_point,
                "/mnt/python_modules"
            ),
            # timeout=Duration.seconds(10),
            # environment={
            #     "PYTHONPATH": "/mnt/dependencies"
            # }            
        )

        check_behaviour_api = apigw.RestApi(
            self, "CheckBehaviourAPI", 
            rest_api_name="CheckBehaviourAPI",
            deploy_options= apigw.StageOptions(
                stage_name="sandbox"
            )
        )

        root_resource = check_behaviour_api.root
        root_get_method = root_resource.add_method(
            "GET",
            apigw.LambdaIntegration(check_behaviour_function),
        )

        check_python_module_import = root_resource.add_resource("check_python_module_import")
        check_python_module_import.add_method(
            "GET",
            apigw.LambdaIntegration(check_behaviour_function),
        )

class CheckConnectivityConstruct(Construct):

    def get_latest_layer_version_arn(self, layer_name: str) -> str:
        lambda_client = boto3.client('lambda')
        response = lambda_client.list_layer_versions(LayerName=layer_name)
        
        if not response['LayerVersions']:
            raise ValueError(f"No versions found for layer: {layer_name}")
        
        # The versions are returned in descending order, so the first one is the latest
        latest_version = response['LayerVersions'][0]
        return latest_version['LayerVersionArn']

    def __init__(self, scope: Construct, id: str, vpc, efs_access_point, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        self.vpc = vpc
        self.efs_access_point = efs_access_point

        check_connectivity_function = _lambda.Function(self, "CheckConnectivityFunction",
            function_name="CheckConnectivityFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="check_connectivity_function.handler",
            code=_lambda.Code.from_asset("lambda-functions/fitness-functions/check-connectivity-function"),
            vpc = self.vpc,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.efs_access_point,
                "/mnt/python_modules"
            ),
            # timeout=Duration.seconds(10),
            # environment={
            #     "PYTHONPATH": "/mnt/dependencies"
            # }            
        )

        latest_layer_version_arn = self.get_latest_layer_version_arn("fitness-function-layer")
        fitness_function_layer = _lambda.LayerVersion.from_layer_version_arn(self, "FitnessFunctionLayer", latest_layer_version_arn)
        check_connectivity_function.add_layers(fitness_function_layer)

        check_connectivity_api = apigw.RestApi(self, "CheckConnectivityAPI", 
            rest_api_name="CheckConnectivityAPI",
            deploy_options= apigw.StageOptions(
                stage_name="sandbox"
            )
        )

        root_resource = check_connectivity_api.root
        root_get_method = root_resource.add_method(
            "GET",
            apigw.LambdaIntegration(check_connectivity_function),
        )

        check_internet_egress = root_resource.add_resource("check_internet_egress")
        check_internet_egress.add_method(
            "GET",
            apigw.LambdaIntegration(check_connectivity_function),
        )

        check_internet_ingress = root_resource.add_resource("check_internet_ingress")
        check_internet_ingress.add_method(
            "GET",
            apigw.LambdaIntegration(check_connectivity_function),
        )

        check_internet_ingress = root_resource.add_resource("check_mysql_database_access")
        check_internet_ingress.add_method(
            "GET",
            apigw.LambdaIntegration(check_connectivity_function),
        )

        check_internet_ingress = root_resource.add_resource("check_api_url_access")
        check_internet_ingress.add_method(
            "GET",
            apigw.LambdaIntegration(check_connectivity_function),
        )

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class SyntrilloClinicBackupStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, efs_file_system, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.efs_file_system = efs_file_system

        backup_vault = backup.BackupVault(
            self, "BackupVault",
            backup_vault_name="syntrillo-clinic-backup-vault",
            removal_policy=RemovalPolicy.DESTROY
        )

        backup_plan = backup.BackupPlan(
            self, "BackupPlan",
            backup_plan_name="syntrillo-clinic-backup-plan",
            backup_vault=backup_vault
        )

        backup_rule = backup_plan.add_rule(
            backup.BackupPlanRule(
                rule_name="DailyBackupRule",
                schedule_expression=events.Schedule.cron(
                    minute="0",
                    hour="5",
                    month="*",
                    week_day="*",
                    year="*"
                ),  # Run daily at 5:00 AM UTC
                )
        )

        backup_plan.add_selection(
            "EfsBackup",
            resources=[
                backup.BackupResource.from_efs_file_system(self.efs_file_system)
            ]
        )

class SyntrilloClinicBackendNetworkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # This creates a VPC with one NAT gateways (N.B. Nat gateways are charged)
        # Nat gateway is necessary for lambda functions to communicates outside the vpc
        # In our case lambdas need to call tenovi and healthie for example
        self.vpc = ec2.Vpc(self, "SyntrilloClinicVPC",
            vpc_name = "SyntrilloClinicVPC",
            nat_gateways=1
        )

        self.hosted_zone = route53.HostedZone.from_hosted_zone_attributes(self, "SyntrilloClinicBackendHostedZone",
            zone_name="sandbox.syntrillo-clinic-backend.com",
            hosted_zone_id="Z00281931X0P3VA26SLKK"
        )

        self.certificate = acm.Certificate( self, "SyntrilloClinicBackendSSLCertificate",
            domain_name="sandbox.syntrillo-clinic-backend.com",
            validation=acm.CertificateValidation.from_dns(self.hosted_zone),
            subject_alternative_names=[
                "api.sandbox.syntrillo-clinic-backend.com"
            ]
        )

class SyntrilloClinicBackendStorageStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc

        self.efs_file_system = efs.FileSystem(self, "SyntrilloClinicEFS",
            vpc=self.vpc,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.efs_access_point = efs.AccessPoint(self, "SyntrilloClinicEFSAccessPoint",
            file_system=self.efs_file_system,
            path="/shared-python-modules", # !! THIS MUST EXIST ON EFS FOR THE LAMBDA TO WORK
            posix_user=efs.PosixUser(
                uid="1001",
                gid="1001"
            )
        )

class SyntrilloClinicBackendDatabaseStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc

        self.db = rds.DatabaseInstance(self, "MySQLDatabase",
            vpc=self.vpc,
            engine=rds.DatabaseInstanceEngine.MYSQL,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc_subnets=ec2.SubnetSelection(subnets=self.vpc.private_subnets),
            multi_az=False,
            allocated_storage=20,
            storage_type=rds.StorageType.GP2,
            credentials=rds.Credentials.from_generated_secret("admin"),
            database_name="syntrillo_clinic_db",
            removal_policy=RemovalPolicy.DESTROY
        )

        db_security_group = self.db.connections.security_groups[0]
    
        db_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(3306),
            "Allow inbound traffic on port 3306 from any IPv4 address"
        )

class SyntrilloClinicIFrameGeneratorStack(Stack):

    def get_latest_layer_version_arn(self, layer_name: str) -> str:
        lambda_client = boto3.client('lambda')
        response = lambda_client.list_layer_versions(LayerName=layer_name)
        
        if not response['LayerVersions']:
            raise ValueError(f"No versions found for layer: {layer_name}")
        
        # The versions are returned in descending order, so the first one is the latest
        latest_version = response['LayerVersions'][0]
        return latest_version['LayerVersionArn'] 
        
    def __init__(self, scope: Construct, id: str, 
            vpc, 
            hosted_zone, 
            certificate, 
            file_system, 
            access_point, 
            **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        self.vpc = vpc
        self.hosted_zone = hosted_zone
        self.certificate = certificate
        self.access_point = access_point
        self.file_system = file_system

        iframe_generator_function = _lambda.Function(self, "IFrameGeneratorFunction",
            function_name="IFrameGeneratorFunction",
            vpc = self.vpc,
            handler="handler.handler",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda-functions/iframe-generator-function"),
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.access_point,
                "/mnt/python_modules"
            ),
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "PYTHONPATH": "/mnt/python_modules"
            },
            tracing=_lambda.Tracing.ACTIVE,
            memory_size=512,
            timeout=Duration.seconds(60),
        )

        iframe_generator_api = apigw.RestApi(self, "IFramGeneratorAPI", 
            rest_api_name="IFramGeneratorAPI",
            domain_name=apigw.DomainNameOptions(
                domain_name="api.sandbox.syntrillo-clinic-backend.com",
                certificate=self.certificate
            ),
            deploy_options= apigw.StageOptions(
                tracing_enabled=True,
                stage_name="sandbox"
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

        # static
        static = root_resource.add_resource("static")

        # -------------------
        # IFRAMES / HTML PAGE
        # -------------------

        # /static/healthie/iframe_provider.css
        static_healthie_iframe_provider_css = static.add_resource("healthie").add_resource("iframe_provider.css")
        static_healthie_iframe_provider_css.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab
        iframe_healthie_provider_tab = root_resource.add_resource("iframe_healthie_provider_tab")
        iframe_healthie_provider_tab.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # /iframe_healthie_provider_tab/healthie/iframe_provider_tab
        healthie_iframe_provider_tab = root_resource.add_resource("healthie").add_resource("iframe_provider_tab")

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

        # ---------------------------------------------------------------------
        # API RESOURCES & METHODES (END)
        # ---------------------------------------------------------------------

        route53.ARecord(self, "SyntrilloCustomDomainARecord", 
            zone=hosted_zone,
            record_name="api.sandbox.syntrillo-clinic-backend.com",
            target=route53.RecordTarget.from_alias(
                route53_targets.ApiGateway(iframe_generator_api)
            )
        )

class SyntrilloClinicBackendFitnessFunctionsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc, efs_access_point, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc
        self.efs_access_point = efs_access_point

        check_connectivity_function=CheckConnectivityConstruct(
            self, "CheckConnectivityConstruct", 
            self.vpc, 
            self.efs_access_point,
        )

        check_behaviour_function=CheckBehaviourConstruct(
            self, "CheckLambdaBehaviourConstruct", 
            self.vpc, 
            self.efs_access_point,
        )

class SyntrilloClinicBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        network=SyntrilloClinicBackendNetworkStack(
            self, "SyntrilloClinicNetworkStack"
        )

        storage=SyntrilloClinicBackendStorageStack(
            self, "SyntrilloClinicStorageStack", 
            network.vpc
        )

        database=SyntrilloClinicBackendDatabaseStack(
            self, "SyntrilloClinicDatabaseStack", 
            network.vpc
        )

        backupStack=SyntrilloClinicBackupStack(
            self, "BackupStack",
            storage.efs_file_system
        )

        fitness_functions=SyntrilloClinicBackendFitnessFunctionsStack(
            self, "FitnessFunctionStack",
            network.vpc,
            storage.efs_access_point,
        )

        iframe_generator=SyntrilloClinicIFrameGeneratorStack(
            self, "IFrameGeneratorStack", 
            vpc=network.vpc, 
            access_point=storage.efs_access_point,
            file_system=storage.efs_file_system, 
            hosted_zone=network.hosted_zone, 
            certificate=network.certificate, 
        )