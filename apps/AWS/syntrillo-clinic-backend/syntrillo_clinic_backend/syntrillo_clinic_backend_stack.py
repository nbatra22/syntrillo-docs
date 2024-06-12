from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3_notifications,
    aws_apigateway as apigw,
    aws_ssm as ssm,
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

class IFrameGeneratorConstruct(Construct):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        iframe_generator_api = apigw.RestApi(self, "IFramGeneratorAPI", rest_api_name="IFramGeneratorAPI")

        # Create the Lambda layers that contains the required libraries
        flask_layer = _lambda.LayerVersion(self, "FlaskLayer",
            layer_version_name="FlaskLayer",
            code=_lambda.Code.from_asset("lambda-layers/flask-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_10],
        )

        # mysql_layer = _lambda.LayerVersion(self, "MySQLLayer",
        #     layer_version_name="MySQLLayer",
        #     code=_lambda.Code.from_asset("lambda-layers/mysql-layer"),
        #     compatible_runtimes=[_lambda.Runtime.PYTHON_3_10],
        # )

        # Create the Lambda function
        iframe_generator_function = _lambda.Function(self, "IFrameGeneratorFunction",
            function_name="IFrameGeneratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda-functions/iframe-generator-function"),
        )

        # Add the Lambda layers to the Lambda function
        iframe_generator_function.add_layers(flask_layer)
        # iframe_generator_function.add_layers(mysql_layer)

        # Add the Lambda function as a REST API resource
        root_resource = iframe_generator_api.root

        any_method = root_resource.add_method(
            "ANY",
            apigw.LambdaIntegration(iframe_generator_function),
        )

        # # Add the Lambda function as a REST API resource (iframe_healthie_provider_tab)
        # iframe_healthie_provider_tab = root_resource.add_resource("iframe_healthie_provider_tab")
        # iframe_healthie_provider_tab.add_method(
        #     "ANY",
        #     apigw.LambdaIntegration(iframe_generator_function),
        # )

        # # Add the Lambda function as a REST API resource (/healthie/iframe_provider_tab/devices)
        # iframe_healthie_provider_tab_devices = root_resource.add_resource("healthie").add_resource("iframe_provider_tab").add_resource("devices_olemaitre")
        # iframe_healthie_provider_tab_devices.add_method(
        #     "ANY",
        #     apigw.LambdaIntegration(iframe_generator_function),
        # )

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
            bucket_name = f"{environment.string_value}.questionnaire-bucket"
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

        LandingPageConstruct(self, "LandingPageConstruct")
        
        IFrameGeneratorConstruct(self, "IFrameGeneratorConstruct")

        UploadQuestionnaireConstruct(self, "UploadQuestionnaireConstruct")