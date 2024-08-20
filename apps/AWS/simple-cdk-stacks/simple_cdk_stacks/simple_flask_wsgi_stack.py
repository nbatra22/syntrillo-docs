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

        self.lambda_function = _lambda.Function(
            self,
            "SimpleLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda/simple_flask_wsgi_function"),
            handler="lambda_function.simple_handler",
        )

        self.api = apigateway.RestApi(
            self,
            "SimpleFlaskWsgiApi",
            rest_api_name="SimpleFlaskWsgiAPI",
            deploy_options=apigateway.StageOptions(stage_name="sandbox"),
        )

        self.api.root.add_method("GET", integration=apigateway.LambdaIntegration(self.lambda_function))

        self.api.root.add_resource("{proxy+}").add_method(
            "GET", integration=apigateway.LambdaIntegration(self.lambda_function)
        )