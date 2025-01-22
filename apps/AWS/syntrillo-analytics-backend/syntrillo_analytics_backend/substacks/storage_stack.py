from aws_cdk import (
    Stack,
    CfnOutput,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
)
from constructs import Construct

class StorageStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.environment_context = environment_context
        
        self.environment_name = self.environment_context["environment-name"]

        removal_policy_value = self.environment_context["storage"]["removal-policy"]
        self.removal_policy = RemovalPolicy[removal_policy_value]

        self.raw_data_bucket = s3.Bucket(
            self, "SyntrilloAnalyticsRawDataBucket",
            bucket_name=f"{self.environment_name}.syntrillo-analytics.raw-data",
            removal_policy=self.removal_policy,
        )

        self.transformed_data_bucket = s3.Bucket(
            self, "SyntrilloAnalyticsTransformedDataBucket",
            bucket_name=f"{self.environment_name}.syntrillo-analytics.transformed-data",
            removal_policy=self.removal_policy,
        )

        CfnOutput(self, "RawDataBucketName", value=self.raw_data_bucket.bucket_name, export_name="RawDataBucketName")
        CfnOutput(self, "RawDataBucketArn", value=self.raw_data_bucket.bucket_arn, export_name="RawDataBucketArn")
        