from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3_notifications,
    aws_apigateway as apigw
)
from constructs import Construct

# -----------------------------------------------------------------------------
# SYNTRILLO BACKEND CUSTOM CONSTRUCTS
# -----------------------------------------------------------------------------
class IFrameGeneratorConstruct(Construct):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    
        iframe_generator_api = apigw.RestApi(self, "IFramGeneratorAPI", rest_api_name="IFramGeneratorAPI")

        # Create the Lambda layer that contains the required libraries
        flask_layer = _lambda.LayerVersion(self, "FlaskLayer",
            layer_version_name="FlaskLayer",
            code=_lambda.Code.from_asset("lambda-layers/flask-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_10],
        )

        # Create the Lambda function
        iframe_generator_function = _lambda.Function(self, "IFrameGeneratorFunction",
            function_name="IFrameGeneratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda-functions/iframe-generator-function"),
        )

        # Add the Lambda layer to the Lambda function
        iframe_generator_function.add_layers(flask_layer)

        # Add the Lambda function as a REST API resource
        root_resource = iframe_generator_api.root

        any_method = root_resource.add_method(
            "ANY",
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

        bucket = s3.Bucket(self, "QuestionnaireBucket",
            bucket_name = "syntrillo-clinic-sandbox.questionnaire-bucket"
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

        IFrameGeneratorConstruct(self, "IFrameGeneratorConstruct")

        UploadQuestionnaireConstruct(self, "UploadQuestionnaireConstruct")