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

import json

class SyntrilloClinicBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.aws_environment = self.node.try_get_context("environment")
        if self.aws_environment == None:
            self.aws_environment = "sandbox"
        
        self.environment_context = self.node.try_get_context(self.aws_environment)

        print("--------------------------------------")
        print(f"SyntrilloBackendStack AWS Environement : <{self.aws_environment}>")
        print(f"")
        print("--------------------------------------")
        print(f"SyntrilloBackendStack AWS Environment Context :")
        print(json.dumps(self.environment_context, indent=4))
        print("--------------------------------------")

        self.network = NetworkStack(
            self, "NetworkStack",
            self.aws_environment
        )

        self.database = DatabaseStack(
            self, "DatabaseStack",
            self.aws_environment,
            vpc=self.network.vpc
        )

        self.storage = StorageStack(
            self, "StorageStack", 
            self.aws_environment,
            vpc=self.network.vpc
        )

        self.secrets = SecretsStack(
            self, "SecretsStack"
        )
        
        self.servers = ServersStack(
            self, "ServersStack", 
            aws_environment=self.aws_environment,
            environment_context=self.environment_context,
            network=self.network,
            database=self.database,
            storage=self.storage,
            secrets=self.secrets,
        )

        self.scheduled_tasks = SyntrilloClinicTaskSchedulingStack(
            self, "TaskSchedulingStack",
            aws_environment=self.aws_environment,
            network=self.network,
            database=self.database,
            storage=self.storage,
            secrets=self.secrets,
            lambda_function=self.servers.iframe_generator_function.function
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