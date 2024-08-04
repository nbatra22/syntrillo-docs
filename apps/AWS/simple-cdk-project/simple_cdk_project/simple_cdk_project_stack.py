from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_lambda as _lambda

class SimpleCdkProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create a lambda function with python 3.9 runtime
        lambda_function = _lambda.Function(
            self,
            "SimpleLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda"),
            handler="lambda_function.lambda_handler",
        )
