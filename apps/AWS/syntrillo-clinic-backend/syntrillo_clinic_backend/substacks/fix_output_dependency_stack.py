from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
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
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

# -----------------------------------------------------------------------------
# STACKS
# -----------------------------------------------------------------------------

class FixOutputDependencyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, stack: Construct, stack2: Construct, stack3: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context

        self.task_scheduling = stack

        ssm.StringParameter(
            self, "TemporaryFixOutputDependencyParameter",
            parameter_name="/tmp/fix_output_dependency",
            string_value=self.task_scheduling.remote_monitoring_data_sync.function_security_group.security_group_id,
        )

        ssm.StringParameter(
            self, "TemporaryFixOutputDependencyParameter2",
            parameter_name="/tmp/fix_output_dependency2",
            string_value=self.task_scheduling.healthie_data_ingestor.function_security_group.security_group_id,
        )

        self.servers = stack2

        if self.environment_context["environment_name"] == 'staging':
            ssm.StringParameter(
                self, "TemporaryFixOutputDependencyParameter3",
                parameter_name="/tmp/fix_output_dependency3",
                string_value=self.servers.blood_pressure_notification_function.function_security_group.security_group_id,
            )

        self.network = stack3

        ssm.StringParameter(
            self, "TemporaryFixOutputDependencyParameter4",
            parameter_name="/tmp/fix_output_dependency4",
            string_value=self.network.bastion_host_security_group.security_group_id,
        )