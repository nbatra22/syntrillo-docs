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
    aws_rds as rds
)
from constructs import Construct

# -----------------------------------------------------------------------------
# SYNTRILLO BACKEND CUSTOM CONSTRUCTS
# -----------------------------------------------------------------------------
class LandingPageConstruct(Construct):
    '''
        This CDK Construct creates a lambda function that serves the landing page.
    '''
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create the Lambda layer that contains the required libraries
        flask_layer = _lambda.LayerVersion(self, "FlaskLayer",
            layer_version_name="FlaskLayer",
            code=_lambda.Code.from_asset("lambda-layers/flask-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_10],
        )

        # Create the Lambda function
        landing_page_function = _lambda.Function(self, "LandingPageFunction",
            function_name="LandingPageFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda-functions/landing-page-function"),
        )

        # Add the Lambda layer to the Lambda function
        landing_page_function.add_layers(flask_layer)

        # Add the Lambda function as a REST API resource
        landing_page_api = apigw.RestApi(self, "LandingPageAPI", rest_api_name="LandingPageAPI")
        landing_page_api_root = landing_page_api.root
        landing_page_api_root.add_method("GET", apigw.LambdaIntegration(landing_page_function))

class CheckingConstruct(Construct):

    def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        self.vpc = vpc

        checking_api = apigw.RestApi(self, "CheckingAPI", rest_api_name="CheckingAPI")

        # Create the Lambda layers that contains the required libraries
        flask_layer = _lambda.LayerVersion(self, "FlaskLayer",
            layer_version_name="FlaskLayer",
            code=_lambda.Code.from_asset("lambda-layers/flask-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_10],
        )

        mysql_layer = _lambda.LayerVersion(self, "MySQLLayer",
            layer_version_name="MySQLLayer",
            code=_lambda.Code.from_asset("lambda-layers/mysql-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_10],
        )

        # Create the Lambda function
        checking_function = _lambda.Function(self, "CheckingFunction",
            function_name="CheckingFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda-functions/checking-function"),
            vpc = self.vpc,
            timeout=Duration.seconds(5)
        )

        # Add the Lambda layers to the Lambda function
        checking_function.add_layers(flask_layer)
        checking_function.add_layers(mysql_layer)

        # Add the Lambda function as a REST API resource
        root_resource = checking_api.root

        any_method = root_resource.add_method(
            "ANY",
            apigw.LambdaIntegration(checking_function),
        )

        # Add resources for tests
        iframe_healthie_provider_tab = root_resource.add_resource("test_network_outside_connectivity")
        iframe_healthie_provider_tab.add_method(
            "ANY",
            apigw.LambdaIntegration(checking_function),
        )

        iframe_healthie_provider_tab = root_resource.add_resource("test_tenovi_access")
        iframe_healthie_provider_tab.add_method(
            "ANY",
            apigw.LambdaIntegration(checking_function),
        )

        iframe_healthie_provider_tab = root_resource.add_resource("register_patient_devices")
        iframe_healthie_provider_tab.add_method(
            "ANY",
            apigw.LambdaIntegration(checking_function),
        )

class IFrameGeneratorConstruct(Construct):

    def __init__(self, scope: Construct, id: str, vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        self.vpc = vpc

        iframe_generator_api = apigw.RestApi(self, "IFramGeneratorAPI", rest_api_name="IFramGeneratorAPI")

        # Create the Lambda layers that contains the required libraries
        flask_layer = _lambda.LayerVersion(self, "FlaskLayer",
            layer_version_name="FlaskLayer",
            code=_lambda.Code.from_asset("lambda-layers/flask-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_10],
        )

        mysql_layer = _lambda.LayerVersion(self, "MySQLLayer",
            layer_version_name="MySQLLayer",
            code=_lambda.Code.from_asset("lambda-layers/mysql-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_10],
        )

        pandas_layer = _lambda.LayerVersion(self, "PandasLayer",
            layer_version_name="PandasLayer",
            code=_lambda.Code.from_asset("lambda-layers/pandas-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_10]
        )

        # Create the Lambda function
        iframe_generator_function = _lambda.Function(self, "IFrameGeneratorFunction",
            function_name="IFrameGeneratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda-functions/iframe-generator-function"),
            vpc = self.vpc,
            timeout=Duration.seconds(5)
        )

        # Add the Lambda layers to the Lambda function
        iframe_generator_function.add_layers(flask_layer)
        iframe_generator_function.add_layers(mysql_layer)
        iframe_generator_function.add_layers(pandas_layer)
        
        # Add the Lambda function as a REST API resource
        root_resource = iframe_generator_api.root

        any_method = root_resource.add_method(
            "ANY",
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

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/devices/tenovi_generate_temporary_pairing_code_form)
        healthie_iframe_provider_tab_devices_tenovi_generate_temporary_pairing_code_form = healthie_iframe_provider_tab_devices.add_resource("tenovi_generate_temporary_pairing_code_form")
        healthie_iframe_provider_tab_devices_tenovi_generate_temporary_pairing_code_form.add_method(
            "POST",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/devices/tenovi_pair_devices_form)
        healthie_iframe_provider_tab_devices_tenovi_pair_devices_form = healthie_iframe_provider_tab_devices.add_resource("tenovi_pair_devices_form")
        healthie_iframe_provider_tab_devices_tenovi_pair_devices_form.add_method(
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

        # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/system_devices)
        healthie_iframe_provider_tab_system_devices = healthie_iframe_provider_tab.add_resource("system_devices")
        healthie_iframe_provider_tab_system_devices.add_method(
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
            subnet_selection=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            )
        )
        
        # Add a security group rule to allow SSH access to the bastion host
        self.bastion_host.connections.allow_from_any_ipv4(
            ec2.Port.tcp(22),
            "Allow SSH access to the bastion host"
        )

        LandingPageConstruct(self, "LandingPageConstruct")
        
        IFrameGeneratorConstruct(self, "IFrameGeneratorConstruct", self.vpc)

        UploadQuestionnaireConstruct(self, "UploadQuestionnaireConstruct")

        CheckingConstruct(self, "CheckingConstruct", self.vpc)
