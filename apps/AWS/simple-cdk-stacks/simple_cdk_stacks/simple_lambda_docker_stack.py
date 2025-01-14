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

class SimpleLambdaDockerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create a lambda function with python 3.10 runtime
        self.lambda_function = _lambda.DockerImageFunction(
            self,
            "SimpleLambdaFunction",
            code=_lambda.DockerImageCode.from_image_asset("lambda/simple_lambda_docker_function"),
        )              


