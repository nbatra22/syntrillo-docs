from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_ssm as ssm,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
    aws_iam as iam
    
)
from constructs import Construct

class SimpleCentralSecretsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create kms key
        self.kms_key = kms.Key(
            self, "SecretKey",
            removal_policy=RemovalPolicy.DESTROY,
            enable_key_rotation=True,
        )

        self.secrets = secretsmanager.Secret(
            self, "secrets",
            encryption_key=self.kms_key,
            
        )

class SimpleLambdaSecretsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, secrets: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.secrets = secrets


        self.lambda_function = _lambda.Function(
            self,
            "SimpleLambdaWithSecretsFunction",
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset("lambda/simple_lambda_with_secrets_function"),
            handler="lambda_function.simple_handler",
            environment={
                "SECRET_1": self.secrets.secrets.secret_arn,
            }
        )

        self.lambda_function.add_to_role_policy(iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
            resources=[self.secrets.secrets.secret_arn],
        ))