from aws_cdk import (
    Stack,
    CfnOutput,
    Fn,
    RemovalPolicy,
    aws_s3 as s3,
    aws_kms as kms,
    aws_iam as iam
)
from constructs import Construct

class StorageStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        
        self.environment_name = self.environment_context["environment-name"]

        removal_policy_value = self.environment_context["storage"]["removal-policy"]
        self.removal_policy = RemovalPolicy[removal_policy_value]



        # Create a KMS key for NON PII Buckets
        encryption_key = kms.Key(self, "SyntrilloAnalyticsBucketsKey",
            enable_key_rotation=True,
            alias=f"syntrillo-analytics-{self.environment_context['environment-name']}-buckets-key",
            description="KMS key for Syntrillo Analytics S3 buckets"
        )

        self.logging_bucket = s3.Bucket(
            self, "SyntrilloAnalyticsS3ServerAccessLogsBucket",
            bucket_name=f"{self.environment_name}.syntrillo-analytics.s3-server-access-logs",
            removal_policy=self.removal_policy,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=encryption_key,
            bucket_key_enabled=True
        )

        self.raw_data_bucket = s3.Bucket( ## !! it's not recommended to enable versionning for dms destinations
            self, "SyntrilloAnalyticsRawDataBucket",
            bucket_name=f"{self.environment_name}.syntrillo-analytics.raw-data",
            removal_policy=self.removal_policy,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=encryption_key,
            bucket_key_enabled=True,
            server_access_logs_bucket=self.logging_bucket     
        )

        self.transformed_data_bucket = s3.Bucket(
            self, "SyntrilloAnalyticsTransformedDataBucket",
            bucket_name=f"{self.environment_name}.syntrillo-analytics.transformed-data",
            removal_policy=self.removal_policy,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=encryption_key,
            bucket_key_enabled=True,
            server_access_logs_bucket=self.logging_bucket
        )


        # Create KMS Access Policy
        quicksight_kms_policy = iam.Policy(self, "SyntrilloAnalyticsStorageKMSAccessPolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Decrypt",
                        # "kms:GenerateDataKey"
                    ],
                    resources=[encryption_key.key_arn]
                )
            ]
        )

        quicksight_role = iam.Role.from_role_arn(
            self, "QuickSightRole",
            role_arn=f"arn:aws:iam::{self.account}:role/service-role/aws-quicksight-service-role-v0"
        )
        quicksight_role.attach_inline_policy(quicksight_kms_policy)

        # PII Bucket

        # Create a KMS key for PII Bucket
        pii_encryption_key = kms.Key(self, "SyntrilloAnalyticsPIIBucketKey",
            enable_key_rotation=True,
            alias=f"syntrillo-analytics-{self.environment_context['environment-name']}-pii-bucket-key",
            description="KMS key for Syntrillo Analytics PII S3 bucket"
        )

        self.pii_data_bucket = s3.Bucket(
            self, "SyntrilloAnalyticsPIIDataBucket",
            bucket_name=f"{self.environment_name}.syntrillo-analytics.pii-data",
            removal_policy=self.removal_policy,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=pii_encryption_key,
            bucket_key_enabled=True,
            server_access_logs_bucket=self.logging_bucket
        )

        # Create KMS Access Policy for PII Data Bucket
        pii_data_bucket_kms_policy = iam.Policy(self, "SyntrilloAnalyticsStorageKMSPIIBucketAccessPolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:GenerateDataKey"
                    ],
                    resources=[pii_encryption_key.key_arn]
                )
            ]
        )

        pii_data_bucket_access_policy = iam.Policy(self, "SyntrilloAnalyticsStoragePIIBucketAccessPolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "s3:PutObject"
                    ],
                    resources=[f"{self.pii_data_bucket.bucket_arn}/patient_piis.csv"]
                )
            ]
        )

        pii_data_sync_function_role_arn=Fn.import_value("PIIDataSyncFunctionRoleArn")
        pii_data_bucket_role = iam.Role.from_role_arn(
            self, "PIIDataSyncFunctionRole",
            role_arn=pii_data_sync_function_role_arn
        )

        pii_data_bucket_role.attach_inline_policy(pii_data_bucket_kms_policy)
        pii_data_bucket_role.attach_inline_policy(pii_data_bucket_access_policy)

        # Create KMS Access Policy
        pii_data_quicksight_kms_policy = iam.Policy(self, "SyntrilloAnalyticsStorageKMSQuickSightAccessPolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "kms:Decrypt",
                        # "kms:GenerateDataKey"
                    ],
                    resources=[pii_encryption_key.key_arn]
                )
            ]
        )

        quicksight_role.attach_inline_policy(pii_data_quicksight_kms_policy)

        # ---------------------------------------------------------------------
        # EXPORT VALUES
        # ---------------------------------------------------------------------        

        CfnOutput(self, "RawDataBucketName", value=self.raw_data_bucket.bucket_name, export_name="RawDataBucketName")
        CfnOutput(self, "RawDataBucketArn", value=self.raw_data_bucket.bucket_arn, export_name="RawDataBucketArn")