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
    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, database: Construct, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        self.environment_name = environment_context["environment_name"]
        self.database = database

        # Create Backup Vault
        removal_policy_value = self.environment_context["backup"]["backup-vault-removal-policy"]
        backup_vault = backup.BackupVault(
            self, "BackupVault",
            backup_vault_name=f"syntrillo-clinic-{self.environment_name}-backup-vault",
            removal_policy=RemovalPolicy[removal_policy_value]
        )

        # Create Backup Plans
        if self.environment_context["backup"]["create-rds-backup-plan"]:
            backup_plan = backup.BackupPlan(
                self, "BackupPlan",
                backup_plan_name=f"syntrillo-clinic-{self.environment_name}-rds-backup-plan",
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
                    delete_after=Duration.days(30)
                    )
            )

            # backup_rule = backup_plan.add_rule(
            #     backup.BackupPlanRule(
            #         rule_name="CopyToAnotherAccount",
            #         copy_actions=[
            #             backup.BackupPlanCopyActionProps(
            #                 destination_backup_vault_arn='arn:aws:backup:us-east-1:058264215756:backup-vault:syntrillo-clinic-prod-copy-vault',
            #                 copy_action_name="CopyToAnotherAccount"
            #             )
            #         ]
            #     )
            # )

            backup_plan.add_selection(
                "MySQLDatabaseFromSnaphotBackup",
                resources=[
                    backup.BackupResource.from_rds_database_instance(self.database.db_from_snapshot)
                ]
            )