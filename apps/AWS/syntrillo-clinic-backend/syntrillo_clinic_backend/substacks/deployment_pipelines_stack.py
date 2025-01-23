from aws_cdk import (
    Stack,
    Fn,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as pipeline_actions,
    aws_codebuild as codebuild,
    SecretValue,
    aws_iam as iam,
    aws_s3 as s3,
    RemovalPolicy
)
from constructs import Construct

class DeploymentPipelinesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, environment_context: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------------------------------------------------------------------
        # IMPORT VALUES
        # ---------------------------------------------------------------------

        github_oauth_token_secrets_name = Fn.import_value('GithubOAuthTokenSecretsName')
        
        # ---------------------------------------------------------------------

        # Create the pipeline
        pipeline = codepipeline.Pipeline(
            self, "DeploymentPipeline",
            pipeline_name="DeploymentPipeline",
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
            oauth_token=SecretValue.secrets_manager(github_oauth_token_secrets_name),
            output=source_output,
        )

        # Add Source Stage
        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        # Create CodeBuild project for CDK deployment
        cdk_build = codebuild.PipelineProject(
            self, "CDKBuild",
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
                    "build": {
                        "commands": [
                            "pwd",
                            "cd ../../PythonAnywhere/website/static/healthie/documents/",
                            "mv questionnaire_template_latest.xlsx questionnaire_template_latest.xlsx.tmp",
                            "ln -s $(cat questionnaire_template_latest.xlsx.tmp) questionnaire_template_latest.xlsx",
                            "rm questionnaire_template_latest.xlsx.tmp",
                            "ls -l",
                            "cd -",
                            "cd lambda-functions/iframe-generator-function/",
                            "mv routes routes.tmp",
                            "mv static static.tmp",
                            "mv syntrillo syntrillo.tmp",
                            "mv templates templates.tmp",
                            "mv api.py api.py.tmp",
                            "mv flask_app.py flask_app.py.tmp",
                            "ln -s $(cat routes.tmp) routes",
                            "ln -s $(cat static.tmp) static",
                            "ln -s $(cat syntrillo.tmp) syntrillo",
                            "ln -s $(cat templates.tmp) templates",
                            "ln -s $(cat api.py.tmp) api.py",
                            "ln -s $(cat flask_app.py.tmp) flask_app.py",
                            "rm routes.tmp static.tmp syntrillo.tmp templates.tmp api.py.tmp flask_app.py.tmp",
                            "ls -l",
                            "cd -",
                            "cd lambda-functions/message-endpoint-function/",
                            "mv routes routes.tmp",
                            "mv static static.tmp",
                            "mv syntrillo syntrillo.tmp",
                            "mv templates templates.tmp",
                            "mv api.py api.py.tmp",
                            "ln -s $(cat routes.tmp) routes",
                            "ln -s $(cat static.tmp) static",
                            "ln -s $(cat syntrillo.tmp) syntrillo",
                            "ln -s $(cat templates.tmp) templates",
                            "ln -s $(cat api.py.tmp) api.py",
                            "rm routes.tmp static.tmp syntrillo.tmp templates.tmp api.py.tmp",
                            "ls -l",
                            "cd -",
                            "cd lambda-functions/blood-pressure-notification-function/",
                            "mv syntrillo syntrillo.tmp",
                            "ln -s $(cat syntrillo.tmp) syntrillo",
                            "rm syntrillo.tmp",
                            "ls -l",
                            "cd -",
                            "cdk diff --role-arn arn:aws:iam::021891579520:role/cdk-prodlike-cfn-exec-role --context 'environment=staging' --require-approval never 2>&1 | tee cdk-diff.txt",
                            "cat cdk-diff.txt |grep 'AWS::Lambda::Function' | cut -d'/' -f2 | tee functions.txt",
                            "cat cdk-diff.txt | grep '\[+\] asset\.[0-9a-z]*$' | grep -o 'asset\.[0-9a-z]*$' | tee assets.txt",
                            "REMOTE_CODE_URL=$(aws lambda get-function --function-name 'IFrameGeneratorFunction' --query 'Code.Location' --output text)",
                            "echo $REMOTE_CODE_URL",
                            "curl -L -o remote_code.zip \"$REMOTE_CODE_URL\"",
                            "unzip -q remote_code.zip -d remote_code",
                            "ls",
                            "diff -r remote_code/ cdk.out/$(sed -n '1p' assets.txt)/ || true",
                            "rm -r remote_code/",
                            "REMOTE_CODE_URL=$(aws lambda get-function --function-name 'MessageEndpointFunction' --query 'Code.Location' --output text)",
                            "echo $REMOTE_CODE_URL",
                            "curl -L -o remote_code.zip \"$REMOTE_CODE_URL\"",
                            "unzip -q remote_code.zip -d remote_code",
                            "ls",
                            "diff -r remote_code/ cdk.out/$(sed -n '2p' assets.txt)/ || true",
                            "rm -r remote_code/",
                            "REMOTE_CODE_URL=$(aws lambda get-function --function-name 'BloodPressureNotificationFunction' --query 'Code.Location' --output text)",
                            "echo $REMOTE_CODE_URL",
                            "curl -L -o remote_code.zip \"$REMOTE_CODE_URL\"",
                            "unzip -q remote_code.zip -d remote_code",
                            "ls",
                            "diff -r remote_code/ cdk.out/$(sed -n '3p' assets.txt)/ || true",
                            "rm -r remote_code/",               
                            "cdk deploy --role-arn arn:aws:iam::021891579520:role/cdk-prodlike-cfn-exec-role --context 'environment=staging' --require-approval never SyntrilloClinicBackendStack/ServersStack" 
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
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0
            )
        )

        # Grant necessary permissions to CodeBuild
        cdk_build.role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:us-east-1:{self.account}:parameter/cdk-bootstrap/hnb659fds/version"]
            )
        )

        cdk_build.role.add_to_policy(
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

        cdk_build.role.add_to_policy(
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

        cdk_build.role.add_to_policy(
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

        cdk_build.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "iam:PassRole"
                ],
                resources=[
                    f"arn:aws:iam::{self.account}:role/cdk-prodlike-cfn-exec-role"
                ]
            )
        )

        cdk_build.role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "lambda:GetFunction"
                ],
                resources=[
                    f"arn:aws:lambda:us-east-1:{self.account}:function:IFrameGeneratorFunction",
                    f"arn:aws:lambda:us-east-1:{self.account}:function:MessageEndpointFunction",
                    f"arn:aws:lambda:us-east-1:{self.account}:function:BloodPressureNotificationFunction",

                ]
            )
        )

        # Create Deploy action
        deploy_action = pipeline_actions.CodeBuildAction(
            action_name="CDK_Deploy",
            project=cdk_build,
            input=source_output,
            run_order=2
        )

        # Create Manual Approval action
        approval_action = pipeline_actions.ManualApprovalAction(
            action_name="Approve_Deployment",
            run_order=1
        )

        # Add Deploy Stage with Approval and Deploy actions
        pipeline.add_stage(
            stage_name="Deploy",
            actions=[approval_action, deploy_action]
        )