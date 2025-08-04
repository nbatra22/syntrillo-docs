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

class BloodPressureAnalysisWorkFlow(Construct):
    def __init__(self, scope: Construct, id: str,
                 lambda_function: _lambda.Function,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create Step Functions tasks
        list_patients_task = tasks.LambdaInvoke(
            self, "ListPatients",
            lambda_function=lambda_function,
            payload=sfn.TaskInput.from_object({
                "action": "list_patients"
            }),
            result_path="$",
            result_selector={
                "users.$": "$.Payload.users",
            }
        )

        analyse_patient_blood_pressure_task = tasks.LambdaInvoke(
            self, "AnalysePatientBloodPressure",
            lambda_function=lambda_function,
            payload=sfn.TaskInput.from_object({
                "action": "analyze_patient_blood_pressure",
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

        map_state.item_processor(analyse_patient_blood_pressure_task)

        # # Add PII sync task
        # pii_sync_task = tasks.LambdaInvoke(
        #     self, "PIISyncTask",
        #     lambda_function=pii_data_sync_function,
        #     payload=sfn.TaskInput.from_object({
        #         "action": "sync_pii"
        #     }),
        #     result_path="$"
        # )

        # Create the state machine
        self.state_machine = sfn.StateMachine(
            self, "BloodPressureAnalysisWorkflow",
            state_machine_name="BloodPressureAnalysisWorkflow",
            definition_body=sfn.DefinitionBody.from_chainable(
                # list_patients_task.next(map_state.next(pii_sync_task))
                list_patients_task.next(map_state)
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
            hour="23",
            month="*",
            day="1,15",
            year="*"
        )

        event_rule = events.Rule(
            self, "BloodPressureAnalysisRule",
            schedule=schedule,
            enabled=False,
        )

        # Add the state machine as a target for the rule
        event_rule.add_target(
            targets.SfnStateMachine(self.state_machine)
        )