from aws_cdk import (
    # Duration,
    Stack,
    RemovalPolicy,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_kms as kms,
    aws_s3 as s3
)
from constructs import Construct

class SimpleRDSS3ExportStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket_name = f'rds-snapshot-syntrillo-clinic-backend-com'

        export_policy = iam.PolicyStatement(
            actions=[
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:PutObject*",
                "s3:GetObject*",
                "s3:DeleteObject*"
            ],
            resources=[
                f"arn:aws:s3:::{bucket_name}",
                f"arn:aws:s3:::{bucket_name}/*"
            ],
            effect=iam.Effect.ALLOW
        )
    
        export_role = iam.Role(
            self, "ExportRole",
            assumed_by=iam.ServicePrincipal("export.rds.amazonaws.com"),
            description="Role for RDS to export snapshots to S3",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonRDSDirectoryServiceAccess")
            ]
        )
        export_role.add_to_policy(export_policy)

        self.kms_key = kms.Key(
            self, "SnapshotKey",
            description="KMS key for encrypting RDS snapshots",
            enabled=True,
            enable_key_rotation=True
        )

        self.kms_key.grant_decrypt(export_role)

        self.bucket = s3.Bucket(
            self, "SnapshotBucket",
            bucket_name=bucket_name,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key
        )