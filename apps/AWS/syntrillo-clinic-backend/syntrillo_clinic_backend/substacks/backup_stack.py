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

class SyntrilloClinicBackupStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, efs_file_system, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.efs_file_system = efs_file_system

        backup_vault = backup.BackupVault(
            self, "BackupVault",
            backup_vault_name="syntrillo-clinic-backup-vault",
            removal_policy=RemovalPolicy.DESTROY
        )

        backup_plan = backup.BackupPlan(
            self, "BackupPlan",
            backup_plan_name="syntrillo-clinic-backup-plan",
            backup_vault=backup_vault
        )

        backup_rule = backup_plan.add_rule(
            backup.BackupPlanRule(
                rule_name="DailyBackupRule",
                schedule_expression=events.Schedule.cron(
                    minute="0",
                    hour="5",
                    month="*",
                    week_day="*",
                    year="*"
                ),  # Run daily at 5:00 AM UTC
                )
        )

        backup_plan.add_selection(
            "EfsBackup",
            resources=[
                backup.BackupResource.from_efs_file_system(self.efs_file_system)
            ]
        )