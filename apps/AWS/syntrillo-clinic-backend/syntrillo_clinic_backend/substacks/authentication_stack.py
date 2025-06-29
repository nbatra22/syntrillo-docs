from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    aws_lambda as _lambda,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_ssm as ssm,
    aws_cognito as cognito,
    aws_apigateway as apigateway,
)
from constructs import Construct

class AuthenticationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_context, **kwargs) -> None:
        super().__init__(scope, construct_id)

        # Create Cognito User Pool
        user_pool = cognito.UserPool(
            self, "SyntrilloClinicUserPool",
            user_pool_name="SyntrilloClinicUserPool",
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            )
        )

        # Create User Pool Client
        user_pool_client = cognito.UserPoolClient(
            self, "SyntrilloClinicUserPoolClient",
            user_pool_client_name="SyntrilloClinicUserPoolClient",
            user_pool=user_pool,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            generate_secret=False
        )

        CfnOutput(self, "SyntrilloClinicAuthenticationUserPoolId", value=user_pool.user_pool_id, export_name="SyntrilloClinic-Authentication-UserPool-Id")