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

        # Cognito User Pool (moved up to be available for Lambda environment variables)
        user_pool = cognito.UserPool(
            self, "SyntrilloClinicUserPool",
            user_pool_name="SyntrilloClinicUserPool",
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False)
            ),
            # Configure password policy for new users
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=False
            ),
            # Configure account recovery settings
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY
        )

        # User Pool Client
        user_pool_client = cognito.UserPoolClient(
            self, "SyntrilloClinicUserPoolClient",
            user_pool=user_pool,
            user_pool_client_name="SyntrilloClinicUserPoolClient",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
                admin_user_password=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True
                ),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE
                ],
                callback_urls=["https://4q497eesgi.execute-api.eu-west-1.amazonaws.com/prod/login.html"]
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ]
        )

        CfnOutput(self, "SyntrilloClinicAuthenticationUserPoolId", value=user_pool.user_pool_id, export_name="SyntrilloClinic-Authentication-UserPool-Id")