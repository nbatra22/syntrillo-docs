from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_ssm as ssm,
    aws_s3 as s3
)
from constructs import Construct

class SimpleDownloadStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        powertools_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "PowertoolsLayer",
            f"arn:aws:lambda:{self.region}:017000801446:layer:AWSLambdaPowertoolsPython:19"
        )

        self.lambda_function = _lambda.Function(
            self,
            "SimpleLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda/simple_download_function"),
            handler="lambda_function.simple_handler",
            layers=[powertools_layer],
        )

        self.api = apigateway.RestApi(
            self,
            "SimpleDownloadApi",
            rest_api_name="SimpleDownloadApi",
            deploy_options=apigateway.StageOptions(stage_name="sandbox"),
            binary_media_types=["*/*"],
        )

        # Create an API Gateway resource and method
        pdf_resource = self.api.root.add_resource("download")
        pdf_integration = apigateway.LambdaIntegration(
            self.lambda_function,
        )
        pdf_resource.add_method("GET", pdf_integration)