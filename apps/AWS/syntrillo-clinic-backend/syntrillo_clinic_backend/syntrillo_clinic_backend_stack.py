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

from syntrillo_clinic_backend.network_stack import NetworkStack

from syntrillo_clinic_backend.database_stack import DatabaseStack
from syntrillo_clinic_backend.storage_stack import StorageStack
from syntrillo_clinic_backend.secrets_stack import SecretsStack

from syntrillo_clinic_backend.servers_stack import ServersStack

from syntrillo_clinic_backend.task_scheduling_stack import SyntrilloClinicTaskSchedulingStack
from syntrillo_clinic_backend.fitness_functions_stack import SyntrilloClinicBackendFitnessFunctionsStack
from syntrillo_clinic_backend.backup_stack import SyntrilloClinicBackupStack

class SyntrilloClinicBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Cannot be self.environment (we get can't set attribute 'environment'), obviously resevered by the cdk
        # self.aws_environment = ssm.StringParameter.from_string_parameter_attributes(
        #     self, "SyntrilloClinicAWSAccountEnvironment",
        #     parameter_name="/syntrillo-clinic/aws/environment"
        # )

        self.aws_environment = 'prod'

        network=NetworkStack(
            self, "NetworkStack",
            self.aws_environment
        )

        database=DatabaseStack(
            self, "DatabaseStack",
            self.aws_environment,
            vpc=network.vpc
        )

        storage=StorageStack(
            self, "StorageStack", 
            self.aws_environment,
            vpc=network.vpc
        )

        secrets=SecretsStack(
            self, "SecretsStack"
        )
        
        servers=ServersStack(
            self, "ServersStack", 
            aws_environment=self.aws_environment,
            network=network,
            database=database,
            storage=storage,
            secrets=secrets,
        )

        scheduled_tasks=SyntrilloClinicTaskSchedulingStack(
            self, "TaskSchedulingStack",
            aws_environment=self.aws_environment,
            network=network,
            database=database,
            storage=storage,
            secrets=secrets,
            lambda_function=servers.iframe_generator_function.function
        )

        # backupStack=SyntrilloClinicBackupStack(
        #     self, "BackupStack",
        #     storage.efs_file_system
        # )

        # fitness_functions=SyntrilloClinicBackendFitnessFunctionsStack(
        #     self, "FitnessFunctionsStack",
        #     vpc=network.vpc,
        #     database=database,
        #     efs_access_point=storage.efs_access_point,
        #     secrets=secrets
        # )