from aws_cdk import (
    Stack,
    Fn,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as pipeline_actions,
    aws_codebuild as codebuild,
    SecretValue,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_s3 as s3,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_codestarnotifications as notifications,
    RemovalPolicy
)
from constructs import Construct

class DeploymentPipelinesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------------------------------------------------------------------
        # IMPORT VALUES
        # ---------------------------------------------------------------------

        github_oauth_token_secrets_arn = Fn.import_value('SyntrilloClinic-Secrets-DeploymentPipeline-GithubOAuthTokenSecrets-Arn')
        
        # ---------------------------------------------------------------------

        # Create the pipeline
        pipeline = codepipeline.Pipeline(
            self, "DeploymentPipeline",
            pipeline_name="DeploymentPipeline",
            pipeline_type=codepipeline.PipelineType.V2,
            execution_mode=codepipeline.ExecutionMode.QUEUED,
            artifact_bucket=s3.Bucket(
                self, "ArtifactBucket",
                bucket_name="staging.syntrillo-clinic-backend.deployment-pipeline.artifacts", 
                auto_delete_objects=True,
                removal_policy=RemovalPolicy.DESTROY
            )
        )

        # Source Stage
        source_output = codepipeline.Artifact()
        source_action = pipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner="Syntrillo",
            repo="SyntrilloClinic",
            branch="staging",
            oauth_token=SecretValue.secrets_manager(github_oauth_token_secrets_arn),
            output=source_output,
        )

        # Add Source Stage
        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        # ---------------------------------------------------------------------
        # Create staging build
        # ---------------------------------------------------------------------

        # Create CodeBuild project for CDK deployment
        cdk_build_staging = codebuild.PipelineProject(
            self, "CDKBuild",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "commands": [
                            "cd apps/AWS/syntrillo-clinic-backend",
                            "npm install -g aws-cdk",
                            "python -m pip install -r requirements.txt",
                            "pip install pytest",
                            "pip install requests"
                        ]
                    },
                    "build": {
                        "commands": [
                            "pwd",
                            "cd utils/deployments",
                            "./symlinks-recreate.sh",       
                            "./diff-local-assets-with-remote-functions.sh staging SyntrilloClinicBackendStack/ServersStack SyntrilloClinicBackendStack/TaskSchedulingStack",
                            "./cdk-deploy-to-staging.sh SyntrilloClinicBackendStack/ServersStack SyntrilloClinicBackendStack/TaskSchedulingStack --require-approval never",
                            "pytest ./test_staging.py --junitxml=./test-reports/report.xml"
                        ]
                    }
                },
                "artifacts": {
                    "files": [
                        "**/*"
                    ],
                    "enable-symlinks": True
                },
                "reports": {
                    "test_reports": {
                    "files": ["report.xml"],
                    "base-directory": "apps/AWS/syntrillo-clinic-backend/utils/deployments/test-reports",
                    "file-format": "JUNITXML"
                }
            }
            }),
            environment=codebuild.BuildEnvironment(
                privileged=True,
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0
            )
        )

        # Grant necessary permissions to CodeBuild
        cdk_build_staging.role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:us-east-1:{self.account}:parameter/cdk-bootstrap/hnb659fds/version"]
            )
        )

        cdk_build_staging.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:PutObject", 
                    "s3:GetObject",
                    "s3:DeleteObject",
                ],
                resources=[
                    f"arn:aws:s3:::cdk-hnb659fds-assets-{self.account}-us-east-1/*"
                ]
            )
        )

        cdk_build_staging.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:List*",
                    "s3:Get*"
                ],
                resources=[
                    f"arn:aws:s3:::cdk-hnb659fds-assets-{self.account}-us-east-1"
                ]
            )
        )

        cdk_build_staging.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudformation:DescribeStacks",
                    "cloudformation:DescribeStackEvents",
                    "cloudformation:GetTemplate",
                    "cloudformation:DescribeChangeSet",
                    "cloudformation:CreateChangeSet",
                    "cloudformation:DeleteChangeSet",
                    "cloudformation:ExecuteChangeSet",
                    "cloudformation:UpdateTerminationProtection"
                ],
                resources=[
                    f"arn:aws:cloudformation:us-east-1:{self.account}:stack/SyntrilloClinicBackendStack*"
                ]
            )
        )

        cdk_build_staging.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "iam:PassRole"
                ],
                resources=[
                    f"arn:aws:iam::{self.account}:role/cdk-prodlike-cfn-exec-role"
                ]
            )
        )

        cdk_build_staging.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "lambda:GetFunction"
                ],
                resources=[
                    f"arn:aws:lambda:us-east-1:{self.account}:function:MessageEndpointFunction",
                    f"arn:aws:lambda:us-east-1:{self.account}:function:PIIDataSyncFunction",
                    f"arn:aws:lambda:us-east-1:{self.account}:function:RemoteMonitoringDataSyncFunction",
                    f"arn:aws:lambda:us-east-1:{self.account}:function:blood_pressure_notifier_handler",
                    f"arn:aws:lambda:us-east-1:{self.account}:function:BloodPressureNotificationFunction",
                    f"arn:aws:lambda:us-east-1:{self.account}:function:IFrameGeneratorFunction",
                    f"arn:aws:lambda:us-east-1:{self.account}:function:HealthieDataIngestorFunction",
                ]
            )
        )

        # ---------------------------------------------------------------------
        # Create prod build
        # ---------------------------------------------------------------------

        prod_cross_account_role_arn = f"arn:aws:iam::381491864638:role/SyntrilloClinicProdCodeBuildDeploymentRole"

        # Create CodeBuild project for CDK deployment
        cdk_build_prod = codebuild.PipelineProject(
            self, "CDKBuildProd",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "commands": [
                            "cd apps/AWS/syntrillo-clinic-backend",
                            "npm install -g aws-cdk",
                            "python -m pip install -r requirements.txt"
                        ]
                    },
                    "pre_build": {
                        "commands": [
                            # Assume the cross-account role for production deployment
                            "temp_role=$(aws sts assume-role --role-arn $CROSS_ACCOUNT_ROLE_ARN --role-session-name ProductionDeploy)",
                            "export AWS_ACCESS_KEY_ID=$(echo $temp_role | jq -r .Credentials.AccessKeyId)",
                            "export AWS_SECRET_ACCESS_KEY=$(echo $temp_role | jq -r .Credentials.SecretAccessKey)",
                            "export AWS_SESSION_TOKEN=$(echo $temp_role | jq -r .Credentials.SessionToken)"
                        ]
                    },
                    "build": {
                        "commands": [
                            "pwd",
                            "cd utils/deployments",       
                            "./diff-local-assets-with-remote-functions.sh prod SyntrilloClinicBackendStack/ServersStack SyntrilloClinicBackendStack/TaskSchedulingStack",
                            "./cdk-deploy-to-staging.sh SyntrilloClinicBackendStack/ServersStack SyntrilloClinicBackendStack/TaskSchedulingStack --require-approval never"
                        ]
                    }
                },
                "artifacts": {
                    "files": [
                        "**/*"
                    ],
                    "enable-symlinks": True
                }
            }),
            environment=codebuild.BuildEnvironment(
                privileged=True,
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                environment_variables={
                    "CROSS_ACCOUNT_ROLE_ARN": codebuild.BuildEnvironmentVariable(value=prod_cross_account_role_arn)
                }
            ),
        )

        # Add necessary permissions to your deployment role
        cdk_build_prod.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "sts:AssumeRole"
                ],
                resources=[
                    prod_cross_account_role_arn
                ]
            )
        )

        # ---------------------------------------------------------------------
        # Add actions to pipeline
        # ---------------------------------------------------------------------

        # Create Deploy action
        build_output = codepipeline.Artifact()
        deploy_to_staging_action = pipeline_actions.CodeBuildAction(
            action_name="CDK_Deploy_to_Staging",
            project=cdk_build_staging,
            input=source_output,
            run_order=1,
            outputs=[build_output]
        )
    
        # Add Deploy Stage with Approval and Deploy actions
        pipeline.add_stage(
            stage_name="DeployToStaging",
            actions=[deploy_to_staging_action]
        )

        # Create Manual Approval action
        approval_prod_action = pipeline_actions.ManualApprovalAction(
            action_name="Approve_Prod_Deployment",
            run_order=1
        )

        # Create Deploy action
        deploy_to_prod_action = pipeline_actions.CodeBuildAction(
            action_name="CDK_Deploy_to_Prod",
            project=cdk_build_prod,
            input=build_output,
            run_order=2
        )

        pipeline.add_stage(
            stage_name="DeployToProd",
            actions=[approval_prod_action, deploy_to_prod_action]
        )

        # ---------------------------------------------------------------------
        # Create a notification rule
        # ---------------------------------------------------------------------

        # # First create an SNS topic
        # notification_topic = sns.Topic(
        #     self, "PipelineNotificationTopic",
        #     topic_name="pipeline-notification-topic"
        # )

        # dev_mailing_list = ssm.StringParameter.from_string_parameter_attributes(
        #     self, "SyntrilloClinicDevMailingList", 
        #     parameter_name="/syntrillo-clinic/dev-mailing-list"
        # ).string_value

        # # Add email subscription to topic
        # notification_topic.add_subscription(
        #     subscriptions.EmailSubscription(dev_mailing_list)
        # )

        notification_topic = sns.Topic.from_topic_arn(
            self, "BackendNotificationsInputTopic",
            Fn.import_value("SyntrilloClinic-BackendNotifications-Input-SNSTopic-Arn")
        )

        # Create a notification rule
        notifications.NotificationRule(
            self, "PipelineNotificationRule",
            detail_type=notifications.DetailType.BASIC,
            events=[
                "codepipeline-pipeline-pipeline-execution-succeeded",
                "codepipeline-pipeline-pipeline-execution-failed",
                "codepipeline-pipeline-stage-execution-succeeded", 
                "codepipeline-pipeline-stage-execution-failed",
            ],
            notification_rule_name="pipeline-notification-rule",
            source=pipeline,
            targets=[notification_topic]                
        )