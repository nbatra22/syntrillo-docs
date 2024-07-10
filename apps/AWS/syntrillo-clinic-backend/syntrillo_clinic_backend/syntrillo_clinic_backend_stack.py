from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
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
)
from constructs import Construct

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

from syntrillo_clinic_backend.network_stack import SyntrilloClinicBackendNetworkStack
from syntrillo_clinic_backend.storage_stack import SyntrilloClinicBackendStorageStack

from syntrillo_clinic_backend.database_stack import SyntrilloClinicBackendDatabaseStack
from syntrillo_clinic_backend.secrets_stack import SyntrilloClinicSecretsStack
from syntrillo_clinic_backend.backup_stack import SyntrilloClinicBackupStack

from syntrillo_clinic_backend.fitness_functions_stack import SyntrilloClinicBackendFitnessFunctionsStack

from syntrillo_clinic_backend.iframe_generator_stack import SyntrilloClinicIFrameGeneratorStack

class SyntrilloClinicBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        network=SyntrilloClinicBackendNetworkStack(
            self, "SyntrilloClinicNetworkStack"
        )

        storage=SyntrilloClinicBackendStorageStack(
            self, "SyntrilloClinicStorageStack", 
            network.vpc
        )

        database=SyntrilloClinicBackendDatabaseStack(
            self, "SyntrilloClinicDatabaseStack", 
            network.vpc
        )

        backupStack=SyntrilloClinicBackupStack(
            self, "BackupStack",
            storage.efs_file_system
        )

        secrets=SyntrilloClinicSecretsStack(
            self, "SecretsStack"
        )

        iframe_generator=SyntrilloClinicIFrameGeneratorStack(
            self, "IFrameGeneratorStack", 
            vpc=network.vpc,
            database=database,
            access_point=storage.efs_access_point,
            file_system=storage.efs_file_system, 
            hosted_zone=network.hosted_zone, 
            certificate=network.certificate,
            secrets=secrets
        )

        fitness_functions=SyntrilloClinicBackendFitnessFunctionsStack(
            self, "FitnessFunctionStack",
            vpc=network.vpc,
            database=database,
            efs_access_point=storage.efs_access_point,
            secrets=secrets
        )