from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    aws_lambda as _lambda,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_ssm as ssm
)
from constructs import Construct

class BackendNotificationsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, environment_context, **kwargs) -> None:
        super().__init__(scope, construct_id)

        # ---------------------------------------------------------------------
        # Lambda + SNS destination
        # ---------------------------------------------------------------------

        # Get destination email
        dev_mailing_list = ssm.StringParameter.from_string_parameter_attributes(
            self, "SyntrilloClinicDevMailingList",
            parameter_name="/syntrillo-clinic/dev-mailing-list"
        ).string_value

        # Create SNS Topic for email notifications
        self.notification_topic = sns.Topic(
            self, "PipelineNotificationTopic",
            topic_name="notifications-output-topic",
        )

        # Add email subscription to the SNS topic
        self.notification_topic.add_subscription(
            sns_subscriptions.EmailSubscription(dev_mailing_list)
        )

        # Create Lambda function for processing pipeline notifications
        self.notification_function = _lambda.Function(
            self, "PipelineNotificationFunction",
            function_name="PipelineNotificationFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda-functions/pipeline-notification-function"),
            timeout=Duration.seconds(30),
            environment={
                "SNS_TOPIC_ARN": self.notification_topic.topic_arn
            }
        )

        # Grant permissions to the Lambda function to publish to SNS
        self.notification_topic.grant_publish(self.notification_function)


        # ---------------------------------------------------------------------
        # Lambda subscription
        # ---------------------------------------------------------------------

        self.notifications_input_topic = sns.Topic(
            self, "NotificationsInputTopic",
            topic_name="notifications-input-topic"
        )

        self.notifications_input_topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("codestar-notifications.amazonaws.com")],
                actions=["sns:Publish"],
                resources=[self.notifications_input_topic.topic_arn]
            )
        )

        self.notifications_input_topic.add_subscription(
            sns_subscriptions.LambdaSubscription(self.notification_function)
        )

        # ---------------------------------------------------------------------
        # OUTPUTS
        # ---------------------------------------------------------------------

        CfnOutput(
            self, "SyntrilloClinicNotificationsInputSNSTopicArn",
            value=self.notifications_input_topic.topic_arn,
            export_name="SyntrilloClinic-BackendNotifications-Input-SNSTopic-Arn"
        )