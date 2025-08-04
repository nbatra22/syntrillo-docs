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