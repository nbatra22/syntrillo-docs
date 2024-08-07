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
            environment={
                "PYTHONPATH": "/mnt/python_modules"
            },          
            timeout=Duration.seconds(10),
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

    def __init__(self, scope: Construct, id: str, vpc, database, efs_access_point, secrets, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        self.vpc = vpc
        self.database = database
        self.secrets = secrets
        self.efs_access_point = efs_access_point

        params_and_secrets = _lambda.ParamsAndSecretsLayerVersion.from_version(_lambda.ParamsAndSecretsVersions.V1_0_103,
            cache_size=500,
            log_level=_lambda.ParamsAndSecretsLogLevel.DEBUG
        )

        check_connectivity_function = _lambda.Function(self, "CheckConnectivityFunction",
            function_name="CheckConnectivityFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="check_connectivity_function.handler",
            params_and_secrets=params_and_secrets,
            code=_lambda.Code.from_asset("lambda-functions/fitness-functions/check-connectivity-function", exclude=['.env']),
            vpc = self.vpc,
            filesystem =_lambda.FileSystem.from_efs_access_point(
                self.efs_access_point,
                "/mnt/python_modules"
            ),
            environment={
                "PYTHONPATH": "/mnt/python_modules",
                "AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN": self.database.secret.secret_arn,
                "AWS_SECRETS_MANAGER_TENOVI_HWI_SECRET_ARN": self.secrets.tenovi_hwi_secrets.secret_arn
            },
            timeout=Duration.seconds(10),
        )

        self.database.secret.grant_read(check_connectivity_function)
        self.secrets.tenovi_hwi_secrets.grant_read(check_connectivity_function)

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

        check_internet_ingress = root_resource.add_resource("check_tenovi_hwi_access")
        check_internet_ingress.add_method(
            "GET",
            apigw.LambdaIntegration(check_connectivity_function),
        )

# -----------------------------------------------------------------------------
# STACK
# -----------------------------------------------------------------------------

class SyntrilloClinicBackendFitnessFunctionsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc, database, efs_access_point, secrets, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc
        self.database = database
        self.efs_access_point = efs_access_point
        self.secrets=secrets

        check_connectivity_function=CheckConnectivityConstruct(
            self, "CheckConnectivityConstruct", 
            self.vpc,
            self.database,
            self.efs_access_point,
            self.secrets
        )

        check_behaviour_function=CheckBehaviourConstruct(
            self, "CheckLambdaBehaviourConstruct", 
            self.vpc,
            self.efs_access_point,
        )