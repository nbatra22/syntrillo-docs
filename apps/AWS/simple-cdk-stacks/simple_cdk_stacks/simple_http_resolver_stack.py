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

class SimpleHttpResolverStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create a lambda function
        self.lambda_function = _lambda.Function(
            self,
            "SimpleHttpResolverLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda/simple_http_resolver_function"),
            handler="lambda_function.handler",
        )

        # latest_layer_version_arn = self.get_latest_layer_version_arn("AWSLambdaPowertoolsPythonV2")
        fitness_function_layer = _lambda.LayerVersion.from_layer_version_arn(
             self, 'PowertoolsLayer',
            "arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:77"
        )

        self.lambda_function.add_layers(fitness_function_layer)

        self.api = apigateway.RestApi(
            self,
            "SimpleHttpResolverApiGateway",
            rest_api_name="SimpleAPI",
            deploy_options=apigateway.StageOptions(stage_name="sandbox"),
        )

        # add get method to the root resource of the api gateway
        self.api.root.add_method("GET", integration=apigateway.LambdaIntegration(self.lambda_function))

        # add hello resource with get method
        hello_resource = self.api.root.add_resource("hello").add_method("GET", integration=apigateway.LambdaIntegration(self.lambda_function))