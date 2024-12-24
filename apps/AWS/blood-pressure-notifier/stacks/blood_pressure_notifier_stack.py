from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_lambda as _lambda
)
from constructs import Construct

class BloodPressureNotifierStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Python Lambda function
        fn = _lambda.Function(
            self,
            "BloodPressureNotifierFunction",
            function_name="blood_pressure_notifier_handler",
            runtime=_lambda.Runtime.PYTHON_3_11,  # Use Python 3.11 runtime
            code=_lambda.Code.from_asset("lambda/blood-pressure-notifier"),  # Code directory containing Python files
            handler="index.lambda_handler",     # Point to handler function in handler.py
        )
        
        # # Create API Gateway
        # api = apigw.LambdaRestApi(
        #     self,
        #     "BloodPressureNotifierApi",
        #     handler=fn,
        #     # rest_api_name="BloodPressureNotifierApi",
        #     # proxy=False  # Disable proxy to define specific routes
        # )

        # # Add resources and methods
        # items = api.root.add_resource("blood-pressure-notifier")
        # items.add_method("POST")   # POST /blood-pressure-notifier
        # items.add_method("GET")    # GET /blood-pressure-notifier
