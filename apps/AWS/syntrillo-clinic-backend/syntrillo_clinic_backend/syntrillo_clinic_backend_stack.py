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

from syntrillo_clinic_backend.substacks.network_stack import NetworkStack

from syntrillo_clinic_backend.substacks.database_stack import DatabaseStack
from syntrillo_clinic_backend.substacks.storage_stack import StorageStack
from syntrillo_clinic_backend.substacks.secrets_stack import SecretsStack

from syntrillo_clinic_backend.substacks.servers_stack import ServersStack

from syntrillo_clinic_backend.substacks.task_scheduling_stack import SyntrilloClinicTaskSchedulingStack
from syntrillo_clinic_backend.substacks.check_functions_stack import SyntrilloClinicBackendCheckFunctionsStack
from syntrillo_clinic_backend.substacks.backup_stack import SyntrilloClinicBackupStack

from syntrillo_clinic_backend.substacks.bastion_stack import SyntrilloClinicBastionStack

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
            environment_context=self.environment_context
        )

        self.database = DatabaseStack(
            self, "DatabaseStack",
            environment_context=self.environment_context,
            network=self.network
        )

        self.storage = StorageStack(
            self, "StorageStack", 
            environment_context=self.environment_context,
            network=self.network
        )

        self.secrets = SecretsStack(
            self, "SecretsStack"
        )
        
        self.servers = ServersStack(
            self, "ServersStack",
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

        if self.aws_environment != "prod":
            self.bastion=SyntrilloClinicBastionStack(
                self, "BastionStack",
                network=self.network,
                database=self.database,
                storage=self.storage,
            )

        backupStack = SyntrilloClinicBackupStack(
            self, "BackupStack",
            environment_context=self.environment_context,
            database=self.database,
        )

        if self.aws_environment == "sandbox":
            check_functions=SyntrilloClinicBackendCheckFunctionsStack(
                self, "CheckFunctionsStack",
                network=self.network,
                database=self.database,
                storage=self.storage,
                secrets=self.secrets
            )