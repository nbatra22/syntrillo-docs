from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_ssm as ssm
)
from constructs import Construct

class SimpleFlaskWsgiStack(Stack):

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
            code=_lambda.Code.from_asset("lambda/simple_flask_wsgi_function"),
            handler="lambda_function.simple_handler",
            layers=[powertools_layer],
        )

        self.api = apigateway.RestApi(
            self,
            "SimpleFlaskWsgiApi",
            rest_api_name="SimpleFlaskWsgiAPI",
            deploy_options=apigateway.StageOptions(stage_name="sandbox"),
            binary_media_types=["*/*"],
        )

        self.api.root.add_method("GET", integration=apigateway.LambdaIntegration(self.lambda_function))

        self.api.root.add_resource("{proxy+}").add_method(
            "GET", integration=apigateway.LambdaIntegration(self.lambda_function,
            proxy=False,
            # request_templates={"application/json": '{ "statusCode": "200" }'},

            # integration_responses=[
            #     apigateway.IntegrationResponse(
            #         status_code="200",
            #         response_templates={"application/json": ''}
            #     )
            # ]

            integration_responses=[
            apigateway.IntegrationResponse(
                status_code="200",
                response_parameters={
                    "method.response.header.Content-Type": "integration.response.header.Content-Type",
                    "method.response.header.Content-Disposition": "integration.response.header.Content-Disposition"
                },
                content_handling=apigateway.ContentHandling.CONVERT_TO_BINARY
            )]

            ),

            # method_responses=[apigateway.MethodResponse(status_code="200")]

            method_responses=[
                apigateway.MethodResponse(
                    status_code="200",
                    response_parameters={
                        "method.response.header.Content-Type": True,
                        "method.response.header.Content-Disposition": True
                    }
                )
            ]

        )