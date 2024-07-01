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
)
from constructs import Construct

# -----------------------------------------------------------------------------
# SYNTRILLO BACKEND CUSTOM CONSTRUCTS
# -----------------------------------------------------------------------------
class LandingPageConstruct(Construct):
    
    def get_latest_layer_version_arn(self, layer_name: str) -> str:
        lambda_client = boto3.client('lambda')
        response = lambda_client.list_layer_versions(LayerName=layer_name)
        
        if not response['LayerVersions']:
            raise ValueError(f"No versions found for layer: {layer_name}")
        
        # The versions are returned in descending order, so the first one is the latest
        latest_version = response['LayerVersions'][0]
        return latest_version['LayerVersionArn'] 
    
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create the Lambda function
        landing_page_function = _lambda.Function(self, "LandingPageFunction",
            function_name="LandingPageFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda-functions/landing-page-function"),
        )

        # retrieve latest arn for lambda layers
        latest_layer_version_arn = self.get_latest_layer_version_arn("flask-layer")
        flask_layer = _lambda.LayerVersion.from_layer_version_arn(self, "FlaskLayer", latest_layer_version_arn)

        # Add the Lambda layer to the Lambda function
        landing_page_function.add_layers(flask_layer)

        # Add the Lambda function as a REST API resource
        landing_page_api = apigw.RestApi(self, "LandingPageAPI", 
            rest_api_name="LandingPageAPI",
            deploy_options= apigw.StageOptions(
                stage_name="sandbox"
            )
        )
        landing_page_api_root = landing_page_api.root
        landing_page_api_root.add_method("GET", apigw.LambdaIntegration(landing_page_function))

class CheckingConstruct(Construct):

    def get_latest_layer_version_arn(self, layer_name: str) -> str:
        lambda_client = boto3.client('lambda')
        response = lambda_client.list_layer_versions(LayerName=layer_name)
        
        if not response['LayerVersions']:
            raise ValueError(f"No versions found for layer: {layer_name}")
        
        # The versions are returned in descending order, so the first one is the latest
        latest_version = response['LayerVersions'][0]
        return latest_version['LayerVersionArn'] 

    def __init__(self, scope: Construct, id: str, vpc, file_system, access_point, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        self.vpc = vpc
        self.access_point = access_point
        self.file_system = file_system

        checking_api = apigw.RestApi(self, "CheckingAPI", 
            rest_api_name="CheckingAPI",
            deploy_options= apigw.StageOptions(
                stage_name="sandbox"
            )
        )

        # Create the Lambda function
        checking_function = _lambda.Function(self, "CheckingFunction",
            function_name="CheckingFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda-functions/checking-function"),
            vpc = self.vpc,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.access_point,
                "/mnt/dependencies"
            ),
            timeout=Duration.seconds(10),
            environment={
                "PYTHONPATH": "/mnt/dependencies"
            }            
        )

        # self.file_system.grant_read_write_access(checking_function)

        # retrieve latest arn for lambda layers
        latest_layer_version_arn = self.get_latest_layer_version_arn("flask-layer")
        flask_layer = _lambda.LayerVersion.from_layer_version_arn(self, "FlaskLayer", latest_layer_version_arn)

        latest_layer_version_arn = self.get_latest_layer_version_arn("mysql-layer")
        mysql_layer = _lambda.LayerVersion.from_layer_version_arn(self, "MySQLLayer", latest_layer_version_arn)

        latest_layer_version_arn = self.get_latest_layer_version_arn("monitoring-layer")
        monitoring_layer = _lambda.LayerVersion.from_layer_version_arn(self, "MonitoringLayer", latest_layer_version_arn)

        latest_layer_version_arn = self.get_latest_layer_version_arn("pandas-layer")
        pandas_layer = _lambda.LayerVersion.from_layer_version_arn(self, "PandasLayer", latest_layer_version_arn)

        latest_layer_version_arn = self.get_latest_layer_version_arn("analytics-layer")
        analytics_layer = _lambda.LayerVersion.from_layer_version_arn(self, "AnalyticsLayer", latest_layer_version_arn)

        # aws_pandas_numpy_layer = _lambda.LayerVersion.from_layer_version_arn(self, "PandasLayer", 'arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python310:16')

        # Add the Lambda layers to the Lambda function
        # checking_function.add_layers(flask_layer)
        # checking_function.add_layers(mysql_layer)
        # checking_function.add_layers(monitoring_layer)
        # checking_function.add_layers(aws_pandas_numpy_layer)
        # checking_function.add_layers(analytics_layer)
        # checking_function.add_layers(pandas_layer)

        # Add the Lambda function as a REST API resource
        root_resource = checking_api.root

        any_method = root_resource.add_method(
            "ANY",
            apigw.LambdaIntegration(checking_function),
        )

        # Add resources for tests
        iframe_healthie_provider_tab = root_resource.add_resource("{id}")
        iframe_healthie_provider_tab.add_method(
            "ANY",
            apigw.LambdaIntegration(checking_function),
        )

import boto3
class IFrameGeneratorConstruct(Construct):
    
    def get_latest_layer_version_arn(self, layer_name: str) -> str:
        lambda_client = boto3.client('lambda')
        response = lambda_client.list_layer_versions(LayerName=layer_name)
        
        if not response['LayerVersions']:
            raise ValueError(f"No versions found for layer: {layer_name}")
        
        # The versions are returned in descending order, so the first one is the latest
        latest_version = response['LayerVersions'][0]
        return latest_version['LayerVersionArn'] 
        
    def __init__(self, scope: Construct, id: str, vpc, hosted_zone, certificate, file_system, access_point, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        self.vpc = vpc
        self.hosted_zone = hosted_zone
        self.certificate = certificate
        self.access_point = access_point
        self.file_system = file_system

        # Create the API Gateway
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

        # Create a Route53 record to map the custom domain to the API Gateway domain
        route53.ARecord(self, "SyntrilloCustomDomainARecord", 
            zone=hosted_zone,
            record_name="api.sandbox.syntrillo-clinic-backend.com",
            target=route53.RecordTarget.from_alias(
                route53_targets.ApiGateway(iframe_generator_api)
            )
        )

        # Create the Lambda function
        iframe_generator_function = _lambda.Function(self, "IFrameGeneratorFunction",
            function_name="IFrameGeneratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda-functions/iframe-generator-function"),
            vpc = self.vpc,
            timeout=Duration.seconds(30),
            memory_size=512,
            tracing=_lambda.Tracing.ACTIVE,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.access_point,
                "/mnt/dependencies"
            ),
            environment={
                "POWERTOOLS_LOG_LEVEL": "DEBUG",
                "PYTHONPATH": "/mnt/dependencies"
            }
        )

        # retrieve latest arn for lambda layers
        latest_layer_version_arn = self.get_latest_layer_version_arn("flask-layer")
        flask_layer = _lambda.LayerVersion.from_layer_version_arn(self, "FlaskLayer", latest_layer_version_arn)

        latest_layer_version_arn = self.get_latest_layer_version_arn("mysql-layer")
        mysql_layer = _lambda.LayerVersion.from_layer_version_arn(self, "MySQLLayer", latest_layer_version_arn)

        latest_layer_version_arn = self.get_latest_layer_version_arn("pandas-layer")
        pandas_layer = _lambda.LayerVersion.from_layer_version_arn(self, "PandasLayer", latest_layer_version_arn)

        latest_layer_version_arn = self.get_latest_layer_version_arn("monitoring-layer")
        monitoring_layer = _lambda.LayerVersion.from_layer_version_arn(self, "MonitoringLayer", latest_layer_version_arn)

        latest_layer_version_arn = self.get_latest_layer_version_arn("analytics-layer")
        analytics_layer = _lambda.LayerVersion.from_layer_version_arn(self, "AnalyticsLayer", latest_layer_version_arn)

        # aws_pandas_numpy_layer = _lambda.LayerVersion.from_layer_version_arn(self, "PandasLayer", 'arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python310:16')

        # Add the Lambda layers to the Lambda function
        # iframe_generator_function.add_layers(flask_layer)
        # iframe_generator_function.add_layers(mysql_layer)
        # iframe_generator_function.add_layers(monitoring_layer)
        # iframe_generator_function.add_layers(analytics_layer)
        # iframe_generator_function.add_layers(pandas_layer)
        # iframe_generator_function.add_layers(aws_pandas_numpy_layer)

        # Add the Lambda function as a REST API resource
        root_resource = iframe_generator_api.root

        any_method = root_resource.add_method(
            "ANY",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add static resources
        static = root_resource.add_resource("static")

        # Add the Lambda function as a REST API resource (/static/healthie/iframe_provider.css)
        static_healthie_iframe_provider_css = static.add_resource("healthie").add_resource("iframe_provider.css")
        static_healthie_iframe_provider_css.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/static/favicon.ico)
        static_favicon_ico = static.add_resource("favicon.ico")
        static_favicon_ico.add_method(
            "GET",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (iframe_healthie_provider_tab)
        iframe_healthie_provider_tab = root_resource.add_resource("iframe_healthie_provider_tab")
        iframe_healthie_provider_tab.add_method(
            "ANY",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab)
        healthie_iframe_provider_tab = root_resource.add_resource("healthie").add_resource("iframe_provider_tab")

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/status)
        healthie_iframe_provider_tab_status = healthie_iframe_provider_tab.add_resource("status")
        healthie_iframe_provider_tab_status.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/devices)
        healthie_iframe_provider_tab_devices = healthie_iframe_provider_tab.add_resource("devices")
        healthie_iframe_provider_tab_devices.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/onboarding)
        healthie_iframe_provider_tab_care_plan = healthie_iframe_provider_tab.add_resource("onboarding")
        healthie_iframe_provider_tab_care_plan.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/care_plan)
        healthie_iframe_provider_tab_care_plan = healthie_iframe_provider_tab.add_resource("care_plan")
        healthie_iframe_provider_tab_care_plan.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/cdss)
        healthie_iframe_provider_tab_cdss = healthie_iframe_provider_tab.add_resource("cdss")
        healthie_iframe_provider_tab_cdss.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/system)
        healthie_iframe_provider_tab_system = healthie_iframe_provider_tab.add_resource("system")
        healthie_iframe_provider_tab_system.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/system/register_patient_at_syntrillo_form)
        healthie_iframe_provider_tab_system_register_patient_at_syntrillo_form = healthie_iframe_provider_tab_system.add_resource("register_patient_at_syntrillo_form")
        healthie_iframe_provider_tab_system_register_patient_at_syntrillo_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/system_devices)
        healthie_iframe_provider_tab_system_devices = healthie_iframe_provider_tab.add_resource("system_devices")
        healthie_iframe_provider_tab_system_devices.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/system_devices/tenovi_dummy_data_generator_form)
        healthie_iframe_provider_tab_system_devices_tenovi_dummy_data_generator_form = healthie_iframe_provider_tab_system_devices.add_resource("tenovi_dummy_data_generator_form")
        healthie_iframe_provider_tab_system_devices_tenovi_dummy_data_generator_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/devices/tenovi_generate_temporary_pairing_code_form)
        healthie_iframe_provider_tab_system_devices_tenovi_generate_temporary_pairing_code_form = healthie_iframe_provider_tab_system_devices.add_resource("tenovi_generate_temporary_pairing_code_form")
        healthie_iframe_provider_tab_system_devices_tenovi_generate_temporary_pairing_code_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/devices/tenovi_pair_devices_form)
        healthie_iframe_provider_tab_system_devices_tenovi_pair_devices_form = healthie_iframe_provider_tab_system_devices.add_resource("tenovi_pair_devices_form")
        healthie_iframe_provider_tab_system_devices_tenovi_pair_devices_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        ) 

class UploadQuestionnaireConstruct(Construct):
    '''
        This CDK Construct creates a questionnaire bucket and a lambda function 
        that listens to the bucket.
        When a questionnaire is uploaded to the bucket, the lambda function
        will call the healthie platform to upload the file.
    '''
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        environment = ssm.StringParameter.from_string_parameter_attributes(
            self, "Environment",
            parameter_name="/environment"
        )

        bucket = s3.Bucket(self, "QuestionnaireBucket",
            bucket_name = f"{environment.string_value}.questionnaire-bucket",
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create the Lambda layer
        pandas_layer = _lambda.LayerVersion(self, "QuestionnaireLayer",
            code=_lambda.Code.from_asset("lambda-layers/pandas-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9]
        )
        
        upload_questionnaire_function = _lambda.Function(self, "UploadQuestionnaireFunction",
            function_name="UploadQuestionnaireFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda-functions/questionnaire-upload-function"),
            timeout=Duration.seconds(10)
        )

        # Add the Lambda layer to the Lambda function
        upload_questionnaire_function.add_layers(pandas_layer)
        
        # Grant the lambda function read and write access to the bucket
        bucket.grant_read_write(upload_questionnaire_function)

        # Add a lambda event trigger to the bucket
        bucket.add_event_notification(s3.EventType.OBJECT_CREATED,
            s3_notifications.LambdaDestination(upload_questionnaire_function)
        )

class SyntrilloClinicBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a VPC with no NAT gateways (Nat gateways are charged)
        self.vpc = ec2.Vpc(self, "SyntrilloClinicVPC",
            vpc_name = "SyntrilloClinicVPC",
            nat_gateways=1
        )

        # Create an EFS file system
        self.file_system = efs.FileSystem(self, "SyntrillClinicEFS",
            vpc=self.vpc,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create an EFS access point
        self.access_point = efs.AccessPoint(self, "SyntrillClinicEFSAccessPoint",
            file_system=self.file_system,
            path="/lambda-dependencies",
            posix_user=efs.PosixUser(
                uid="1001",
                gid="1001"
            )
        )

        # Create db instance
        self.db = rds.DatabaseInstance(self, "MySQLDatabase",
            engine=rds.DatabaseInstanceEngine.MYSQL,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=self.vpc.private_subnets),
            multi_az=False,
            allocated_storage=20,
            storage_type=rds.StorageType.GP2,
            credentials=rds.Credentials.from_generated_secret("admin"),
            database_name="syntrillo_clinic_db",
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Get the security group associated with the RDS database instance
        db_security_group = self.db.connections.security_groups[0]

        # Add an inbound rule to the RDS database security group
        # to allow traffic from any IP address
        db_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(3306),
            "Allow inbound traffic on port 3306 from any IPv4 address"
        )
        
        # Create a bastion host in the public subnet
        self.bastion_host = ec2.BastionHostLinux(self, "BastionHost",
            vpc=self.vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            subnet_selection=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            # init=ec2.CloudFormationInit.from_config_sets(
            #     config_sets={
            #         "default": ["install_packages", "run_commands"]
            #     },
            #     configs={
            #         "install_packages": ec2.InitConfig([
            #             ec2.InitPackage.yum("mysql"),
            #         ]),
            #         "run_commands": ec2.InitConfig([
            #             ec2.InitCommand.shell_command("echo 'Hello from the bastion host!' > /tmp/message.txt")
            #         ])
            #     }
            # ),
            # init_options=ec2.ApplyCloudFormationInitOptions(
            #     config_sets=["default"]
            # ),
        )
        
        # Add a security group rule to allow SSH access to the bastion host
        # self.bastion_host.connections.allow_from_any_ipv4(
        #     ec2.Port.tcp(22),
        #     "Allow SSH access to the bastion host"
        # )

        self.file_system.connections.allow_from(self.bastion_host, ec2.Port.tcp(2049))
        self.file_system.grant_read_write(self.bastion_host)
        #self.access_point.grant_read_write(self.bastion_host)


        # Reference an existing hosted zone using its attributes
        hosted_zone = route53.HostedZone.from_hosted_zone_attributes(self, "SyntrilloClinicBackendHostedZone",
            zone_name="sandbox.syntrillo-clinic-backend.com",
            hosted_zone_id="Z00281931X0P3VA26SLKK"
        )
        self.hosted_zone = hosted_zone

        # Create a certificate for the domain
        certificate = acm.Certificate( self, "SyntrilloClinicBackendSSLCertificate",
            domain_name="sandbox.syntrillo-clinic-backend.com",
            validation=acm.CertificateValidation.from_dns(self.hosted_zone),
            subject_alternative_names=[
                "api.sandbox.syntrillo-clinic-backend.com"
            ]
        )
        self.certificate = certificate

        LandingPageConstruct(self, "LandingPageConstruct")
        
        IFrameGeneratorConstruct(self, "IFrameGeneratorConstruct", self.vpc,  self.hosted_zone, self.certificate, self.file_system, self.access_point)

        UploadQuestionnaireConstruct(self, "UploadQuestionnaireConstruct")

        CheckingConstruct(self, "CheckingConstruct", self.vpc, self.file_system, self.access_point)
