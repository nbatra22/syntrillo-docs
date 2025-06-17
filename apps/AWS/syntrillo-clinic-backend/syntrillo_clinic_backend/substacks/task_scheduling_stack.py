from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    Fn,
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
    aws_events_targets as targets,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)
from constructs import Construct

# -----------------------------------------------------------------------------
# CONSTRUCTS
# -----------------------------------------------------------------------------
from syntrillo_clinic_backend.constructs.tasks.remote_monitoring_datasync_function_construct import RemoteMonitoringDataSync
from syntrillo_clinic_backend.constructs.tasks.pii_datasync_function_construct import PIIDataSync
from syntrillo_clinic_backend.constructs.tasks.healthie_data_ingestor_function_construct import HealthieDataIngestor
from syntrillo_clinic_backend.constructs.tasks.candid_billing_ingestor_function_construct import CandidBillingIngestor

class DataSyncWorkflow(Construct):
    def __init__(self, scope: Construct, id: str,
                 remote_monitoring_data_sync_function: _lambda.Function,
                 pii_data_sync_function: _lambda.Function,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create Step Functions tasks
        list_patients_task = tasks.LambdaInvoke(
            self, "ListPatients",
            lambda_function=remote_monitoring_data_sync_function,
            payload=sfn.TaskInput.from_object({
                "action": "list_patients"
            }),
            result_path="$",
            result_selector={
                "users.$": "$.Payload.users",
            }
        )

        sync_patient_task = tasks.LambdaInvoke(
            self, "SyncPatientData",
            lambda_function=remote_monitoring_data_sync_function,
            payload=sfn.TaskInput.from_object({
                "action": "sync_patient",
                "id.$": "$.id"
            }),
            result_path="$",
            result_selector={
                "success.$": "$.Payload.success",
                "error.$": "$.Payload.error"
            }
        )

        # Create Map state for processing patients
        map_state = sfn.Map(
            self, "ProcessEachPatient",
            max_concurrency=5,
            items_path="$.users"
        )

        map_state.item_processor(sync_patient_task)

        # Add PII sync task
        pii_sync_task = tasks.LambdaInvoke(
            self, "PIISyncTask",
            lambda_function=pii_data_sync_function,
            payload=sfn.TaskInput.from_object({
                "action": "sync_pii"
            }),
            result_path="$"
        )

        # Create the state machine
        self.state_machine = sfn.StateMachine(
            self, "StepFunctionsDataSyncWorkflow",
            state_machine_name="StepFunctionsDataSyncWorkflow",
            definition_body=sfn.DefinitionBody.from_chainable(
                list_patients_task.next(map_state.next(pii_sync_task))
            ),
            timeout=Duration.minutes(30),
            tracing_enabled=True
        )

        # Create a scheduled event rule
        # we prefer a cron expression instead of a rate, because with a rate we do not know exactly when
        # the lambda is triggered. With cron, you can decide exactly when you start.
        # This avoids using database resources during working hours
        schedule = events.Schedule.cron(
            minute="0",
            hour="0/6",
            month="*",
            week_day="*",
            year="*",
        )

        event_rule = events.Rule(
            self, "RemoteMonitoringDataSyncRule",
            schedule=schedule,
            enabled=True,
        )

        # Add the state machine as a target for the rule
        event_rule.add_target(
            targets.SfnStateMachine(self.state_machine)
        )


class HealthieDataIngestorWorkFlow(Construct):
    def __init__(self, scope: Construct, id: str,
                 lambda_function: _lambda.Function,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create the Lambda task
        process_task = tasks.LambdaInvoke(
            self, "FetchHealthieData", 
            lambda_function=lambda_function,
            payload=sfn.TaskInput.from_object({
                "action": "process"
            })
        )

        # Create the state machine
        self.state_machine = sfn.StateMachine(
            self, "HealthieDataIngestorWorkFlow",
            state_machine_name="HealthieDataIngestorWorkFlow", 
            definition_body=sfn.DefinitionBody.from_chainable(process_task),
            timeout=Duration.minutes(5),
            tracing_enabled=True
        )

        # # Create a scheduled event rule
        # # we prefer a cron expression instead of a rate, because with a rate we do not know exactly when
        # # the lambda is triggered. With cron, you can decide exactly when you start.
        # # This avoids using database resources during working hours
        schedule = events.Schedule.cron(
            minute="0",
            hour="0/6",
            month="*",
            week_day="*",
            year="*",
        )

        event_rule = events.Rule(
            self, "HealthieDataIngestorWorkFlowSyncRule",
            schedule=schedule,
            enabled=True,
        )

        # Add the state machine as a target for the rule
        event_rule.add_target(
            targets.SfnStateMachine(self.state_machine)
        )

class CandidBillingIngestorWorkFlow(Construct):
    def __init__(self, scope: Construct, id: str,
                 lambda_function: _lambda.Function,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create the Lambda task
        process_task = tasks.LambdaInvoke(
            self, "FetchCandidBilling", 
            lambda_function=lambda_function,
            payload=sfn.TaskInput.from_object({
                "action": "process"
            })
        )

        # Create the state machine
        self.state_machine = sfn.StateMachine(
            self, "CandidBillingIngestorWorkFlow",
            state_machine_name="CandidBillingIngestorWorkFlow", 
            definition_body=sfn.DefinitionBody.from_chainable(process_task),
            timeout=Duration.minutes(5),
            tracing_enabled=True
        )

        # # Create a scheduled event rule
        # # we prefer a cron expression instead of a rate, because with a rate we do not know exactly when
        # # the lambda is triggered. With cron, you can decide exactly when you start.
        # # This avoids using database resources during working hours
        schedule = events.Schedule.cron(
            minute="0",
            hour="0/6",
            month="*",
            week_day="*",
            year="*",
        )

        event_rule = events.Rule(
            self, "CandidBillingIngestorWorkFlowSyncRule",
            schedule=schedule,
            enabled=True,
        )

        # Add the state machine as a target for the rule
        event_rule.add_target(
            targets.SfnStateMachine(self.state_machine)
        )

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------
class SyntrilloClinicTaskSchedulingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, 
                 environment_context: dict,
                 network: Construct, 
                 database: Construct,
                 storage: Construct,
                 secrets: Construct,
                 lambda_function: _lambda.Function, 
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.aws_environment = environment_context["environment_name"]
        self.network = network
        self.database = database
        self.storage = storage
        self.secrets = secrets

        self.termination_protection = self.environment_context["stacks-termination-protection"]

        self.remote_monitoring_data_sync = RemoteMonitoringDataSync(
            self, "RemoteMonitoringDataSyncFunction",
            aws_environment=self.aws_environment,
            network=self.network,
            database=self.database,
            storage=self.storage,
            secrets=self.secrets,
        )

        pii_data_sync = PIIDataSync(
            self, "PIIDataSyncFunction",
            aws_environment=self.aws_environment,
            network=self.network,
            database=self.database,
            storage=self.storage,
            secrets=self.secrets,
        )

        data_sync_workflow = DataSyncWorkflow(
            self, "DataSyncFunction",
            remote_monitoring_data_sync_function = self.remote_monitoring_data_sync.remote_monitoring_data_sync_function,
            pii_data_sync_function = pii_data_sync.pii_data_sync_function,
        )

        self.healthie_data_ingestor = HealthieDataIngestor(
            self, "HealthieDataIngestor",
            aws_environment=self.aws_environment,
            network=self.network,
            database=self.database,
            storage=self.storage,
            secrets=self.secrets,
        )

        self.healthie_data_ingestor_worflow = HealthieDataIngestorWorkFlow(
            self, "HealthieDataIngestorWorkFlow",
            lambda_function=self.healthie_data_ingestor.healthie_data_ingestor_function
        )


        if self.aws_environment == "staging":        
            self.candid_billing_ingestor = CandidBillingIngestor(
                self, "CandidBillingIngestor",
                aws_environment=self.aws_environment,
                network=self.network,
                database=self.database,
                storage=self.storage,
                secrets=self.secrets,
            )

            self.candid_billing_ingestor_worflow = CandidBillingIngestorWorkFlow(
                self, "CandidBillingIngestorWorkFlow",
                lambda_function=self.candid_billing_ingestor.candid_billing_ingestor_function
            )