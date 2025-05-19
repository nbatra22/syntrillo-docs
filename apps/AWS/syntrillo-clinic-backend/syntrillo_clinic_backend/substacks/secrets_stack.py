from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3_notifications,
    aws_apigateway as apigw,
    aws_ssm as ssm,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_certificatemanager as acm,
    aws_efs as efs,
    aws_backup as backup,
    aws_efs as efs,
    aws_events as events,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
)
from constructs import Construct

import json

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class SecretsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------------------------------------------------------------------
        # INPUTS
        # ---------------------------------------------------------------------
        self.environment_context = environment_context

        self.termination_protection = self.environment_context["stacks-termination-protection"]
 
        db_host_param = ssm.StringParameter.from_string_parameter_name(self, "ServersStackDatabaseHostParameter", "/syntrillo-clinic/aws/db/host").string_value

        # ---------------------------------------------------------------------
        # Create Custom KMS Key for all the secrets
        # ---------------------------------------------------------------------
        custom_kms_key = kms.Key(
            self, "SecretsKmsKey",
            description="Custom KMS key for Secrets",
            enabled=True,
            enable_key_rotation=True,
            pending_window=Duration.days(30)
        )

        # ---------------------------------------------------------------------
        # Create Database Credentials
        # ---------------------------------------------------------------------

        # Create IFrames & Sync functions access secrets
        self.database_lambda_user_secrets = secretsmanager.Secret(
            self, "DatabaseLambdaUserSecrets",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({
                    "username": "syntrillo_clinic_lambda_user",
                    "host": db_host_param
                }),
                generate_string_key="password",
                exclude_characters='/@"\\',
                include_space=False,
                password_length=32
            ),
            encryption_key=custom_kms_key
        )

        # Create DMS access secrets
        self.database_dms_user_secrets = secretsmanager.Secret(
            self, "DatabaseDMSUserSecrets",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({
                    "username": "syntrillo_analytics_dms_user",
                    "host": db_host_param,
                    "port": "3306",
                    "database": "syntrillo$HealthInformation"
                }),
                generate_string_key="password",
                exclude_characters=';.:+{}',
                include_space=False,
                password_length=32
            ),
            encryption_key=custom_kms_key
        )

        # ---------------------------------------------------------------------
        # Create Third party API Keys secrets
        # ---------------------------------------------------------------------
        self.tenovi_hwi_secrets = secretsmanager.Secret(
            self, "TenoviHWISecrets",
            encryption_key=custom_kms_key
        )

        self.healthie_secrets = secretsmanager.Secret(
            self, "HealthieSecrets",
            encryption_key=custom_kms_key
        )

        self.openai_secrets = secretsmanager.Secret(
            self, "OpenAiSecrets",
            encryption_key=custom_kms_key
        )

        # ---------------------------------------------------------------------
        # Create certificates & OAuth token secrets
        # ---------------------------------------------------------------------
        self.database_certificate = secretsmanager.Secret(
            self, "DatabaseCertificate",
            encryption_key=custom_kms_key
        )

        self.github_oauth_token = secretsmanager.Secret(
            self, "GithubOAuthToken",
            encryption_key=custom_kms_key
        )

        # ---------------------------------------------------------------------
        # Create healthie ids secrets
        # ---------------------------------------------------------------------
        self.healthie_ids_secrets = secretsmanager.Secret(
            self, "HealthieIDsSecrets",
            encryption_key=custom_kms_key
        )

        # ---------------------------------------------------------------------
        # OUTPUTS
        # ---------------------------------------------------------------------
        # CfnOutput(
        #     self, "SecretsDatabaseLambdaUserSecretsArn", # TO DELETE
        #     value=self.database_lambda_user_secrets.secret_arn,
        #     export_name="Secrets-Database-LambdaUserSecrets-Arn"
        # )



        # CfnOutput(
        #     self, "SecretsTenoviHwiSecretsArn",  # TO DELETE
        #     value=self.tenovi_hwi_secrets.secret_arn,
        #     export_name="Secrets-TenoviHwiSecrets-Arn"
        # )


        # CfnOutput(
        #     self, "SecretsHealthieSecretsArn",  # TO DELETE
        #     value=self.healthie_secrets.secret_arn,
        #     export_name="Secrets-HealthieSecrets-Arn"
        # )



        # CfnOutput(
        #     self, "SecretsOpenAiSecretsArn",  # TO DELETE
        #     value=self.openai_secrets.secret_arn,
        #     export_name="Secrets-OpenAiSecrets-Arn"
        # )



        # CfnOutput(
        #     self, "SecretsCutomKMSKeyArn",  # TO DELETE
        #     value=custom_kms_key.key_arn,
        #     export_name="Secrets-SecretsKMSKey-Arn"
        # )

        # ---

        CfnOutput(
            self, "SyntrilloClinicSecretsDatabaseLambdaUserSecretsArn",
            value=self.database_lambda_user_secrets.secret_arn,
            export_name="SyntrilloClinic-Secrets-Database-LambdaUserSecrets-Arn"
        )
        CfnOutput(
            self, "SyntrilloClinicSecretsTenoviHwiSecretsArn",
            value=self.tenovi_hwi_secrets.secret_arn,
            export_name="SyntrilloClinic-Secrets-TenoviHwiSecrets-Arn"
        )

        CfnOutput(
            self, "SyntrilloClinicSecretsHealthieSecretsArn",
            value=self.healthie_secrets.secret_arn,
            export_name="SyntrilloClinic-Secrets-HealthieSecrets-Arn"
        )

        CfnOutput(
            self, "SyntrilloClinicSecretsOpenAiSecretsArn",
            value=self.openai_secrets.secret_arn,
            export_name="SyntrilloClinic-Secrets-OpenAiSecrets-Arn"
        )

        CfnOutput(
            self, "SyntrilloClinicSecretsCutomKMSKeyArn",
            value=custom_kms_key.key_arn,
            export_name="SyntrilloClinic-Secrets-SecretsKMSKey-Arn"
        )

        # ---

        # CfnOutput(
        #     self, "DatabaseCertificateSecretArn", # TO DELETE
        #     value=self.database_certificate.secret_arn, 
        #     export_name="DatabaseCertificateSecretArn"
        # )

        # CfnOutput(
        #     self, "DatabaseDMSUserSecretsArn", # TO DELETE
        #     value=self.database_dms_user_secrets.secret_arn, 
        #     export_name="DatabaseDMSUserSecretsArn"
        # )

        # CfnOutput(
        #     self, "GithubOAuthTokenSecretsName", # TO DELETE - WAIT!!!
        #     value=self.github_oauth_token.secret_name, 
        #     export_name="GithubOAuthTokenSecretsName"
        # )

        # ---

        CfnOutput(
            self, "SyntrilloClinicSecretsDatabaseDMSUserSecretsArn", 
            value=self.database_dms_user_secrets.secret_arn, 
            export_name="SyntrilloClinic-Secrets-Database-DMSUserSecrets-Arn"
        )

        CfnOutput(
            self, "SyntrilloClinicSecretsDatabaseCertificateSecretsArn", 
            value=self.database_certificate.secret_arn, 
            export_name="SyntrilloClinic-Secrets-Database-CertificateSecrets-Arn"
        )        

        CfnOutput(
            self, "SyntrilloClinicSecretsDeploymentGithubOAuthTokenSecretsArn", 
            value=self.github_oauth_token.secret_arn, 
            export_name="SyntrilloClinic-Secrets-DeploymentPipeline-GithubOAuthTokenSecrets-Arn"
        )

        CfnOutput(
            self, "SyntrilloClinicSecretsFunctionsHealthieIDsSecrets", 
            value=self.healthie_ids_secrets.secret_arn, 
            export_name="SyntrilloClinic-Secrets-Functions-HealthieIDsSecrets-Arn"
        )