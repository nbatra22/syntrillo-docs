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
# FUNCTION CONSTRUCTS
# -----------------------------------------------------------------------------
from syntrillo_clinic_backend.constructs.tasks.remote_monitoring_datasync_function_construct import RemoteMonitoringDataSync
from syntrillo_clinic_backend.constructs.tasks.pii_datasync_function_construct import PIIDataSync
from syntrillo_clinic_backend.constructs.tasks.healthie_data_ingestor_function_construct import HealthieDataIngestor
from syntrillo_clinic_backend.constructs.tasks.candid_billing_ingestor_function_construct import CandidBillingIngestor
from syntrillo_clinic_backend.constructs.tasks.blood_pressure_analysis_function_construct import BloodPressureAnalysis

# -----------------------------------------------------------------------------
# WORKFLOW CONSTRUCTS
# -----------------------------------------------------------------------------
from syntrillo_clinic_backend.constructs.workflows.blood_pressure_analysis_workflow_construct import BloodPressureAnalysisWorkFlow
from syntrillo_clinic_backend.constructs.workflows.candid_billing_ingestor_workflow_construct import CandidBillingIngestorWorkFlow
from syntrillo_clinic_backend.constructs.workflows.healthie_data_ingestor_workflow_construct import HealthieDataIngestorWorkFlow
from syntrillo_clinic_backend.constructs.workflows.datasync_workflow_construct import DataSyncWorkflow

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

        # ---------------------------------------------------------------------
        # REMOTE MONITORING DATA SYNC
        # ---------------------------------------------------------------------

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
            remote_monitoring_data_sync_function = self.remote_monitoring_data_sync.function,
            pii_data_sync_function = pii_data_sync.function,
        )

        # ---------------------------------------------------------------------
        # HEALTHIE DATA INGESTOR
        # ---------------------------------------------------------------------

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
            lambda_function=self.healthie_data_ingestor.function
        )

        # ---------------------------------------------------------------------
        # CANDID BILLING INGESTOR
        # ---------------------------------------------------------------------

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
            lambda_function=self.candid_billing_ingestor.function
        )

        # ---------------------------------------------------------------------
        # BLOOD PRESSURE ANALYSIS
        # ---------------------------------------------------------------------

        # if self.aws_environment == "staging" or self.aws_environment == "sandbox" :
        
        self.blood_pressure_analysis = BloodPressureAnalysis(
            self, "BloodPressureAnalysis",
            aws_environment=self.aws_environment,
            network=self.network,
            database=self.database,
            storage=self.storage,
            secrets=self.secrets,
        )

        self.blood_pressure_analysis_worflow = BloodPressureAnalysisWorkFlow(
            self, "BloodPressureAnalysisWorkFlow",
            lambda_function=self.blood_pressure_analysis.function,
        )
