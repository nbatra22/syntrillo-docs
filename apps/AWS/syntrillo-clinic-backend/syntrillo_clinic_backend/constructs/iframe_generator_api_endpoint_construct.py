from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    ArnFormat,
    aws_lambda_event_sources as event_sources,
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
    aws_iam as iam,
    aws_logs as logs,
    aws_wafv2 as wafv2,
)
from constructs import Construct

from aws_cdk import Stack, CfnOutput
from constructs import Construct
import aws_cdk.aws_apigateway as apigateway
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_ssm as ssm

class IFrameGeneratorApiEndpoint(Construct):
    def __init__(self, scope: Construct, id: str, environment_context: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.environment_context = environment_context
        self.environment_name = self.environment_context["environment_name"]

        self.hosted_zone = self._setup_hosted_zone()
        self.certificate = self._setup_ssl_certificate()
        self.log_destination = self._setup_log_destination()
        self.rest_api = self._setup_api_gateway()

        if self.environment_context["iframe_generator_api"]["use_waf"]:
            self.waf_webacl = self._setup_waf_webacl()

    def _setup_waf_webacl(self):
        webacl_log_group_removal_policy_value = self.environment_context["iframe_generator_api"]["webacl-log-group-removal-policy"]
        webacl_log_group = logs.LogGroup(
            self, "IFramGeneratorAPIWebAclLogGroup",
            log_group_name="aws-waf-logs-IFramGeneratorAPIWebAclLogging",
            # Loggroup name must folow a specific format and can not finish with '*' 
            # (https://docs.aws.amazon.com/waf/latest/developerguide/logging-cw-logs.html#logging-cw-logs-naming)
            removal_policy=RemovalPolicy[webacl_log_group_removal_policy_value]
        )

        web_acl = wafv2.CfnWebACL(
            self, "IFramGeneratorAPIWebAcl",
            name="IFramGeneratorAPIWebAcl",
            scope="REGIONAL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(
                allow={}
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                sampled_requests_enabled=True,
                metric_name="IFramGeneratorAPIWebAclMetrics"
            ),
        )

        # Enable logging for the Web ACL using CfnLoggingConfiguration
        logging_configuration = wafv2.CfnLoggingConfiguration(
            self, "IFramGeneratorAPIWebAclLoggingConfiguration",
            resource_arn=web_acl.attr_arn,
            log_destination_configs=[     
                # Loggroup name must folow a specific format and can not finish with '*' 
                # (https://docs.aws.amazon.com/waf/latest/developerguide/logging-cw-logs.html#logging-cw-logs-naming)
                # therfore we cannot use webacl_log_group.log_group_arn directly in this destination config list        
                Stack.of(self).format_arn(
                arn_format=ArnFormat.COLON_RESOURCE_NAME,
                service="logs",
                resource="log-group",
                resource_name=webacl_log_group.log_group_name,
            )]
        )

        web_acl_association = wafv2.CfnWebACLAssociation(
            self, "IFramGeneratorAPIWebAclAssociation",
            resource_arn=self.rest_api.deployment_stage.stage_arn,
            web_acl_arn=web_acl.attr_arn
        )

        allowed_referer = self.environment_context["iframe_generator_api"]["allowed_referer"]
        sepcific_referer_rule = wafv2.CfnWebACL.RuleProperty(
            name="IFramGeneratorAPIWebAclAllowSpecificRefererRule",
            priority=1,
            action=wafv2.CfnWebACL.RuleActionProperty(
                block={}
            ),
            statement=wafv2.CfnWebACL.StatementProperty(
                not_statement=wafv2.CfnWebACL.NotStatementProperty(
                    statement=wafv2.CfnWebACL.StatementProperty(
                        byte_match_statement=wafv2.CfnWebACL.ByteMatchStatementProperty(
                            field_to_match=wafv2.CfnWebACL.FieldToMatchProperty(
                                single_header=wafv2.CfnWebACL.SingleHeaderProperty(
                                    name="referer"
                                )
                            ),
                            positional_constraint="CONTAINS",
                            search_string=allowed_referer,
                            text_transformations=[
                                wafv2.CfnWebACL.TextTransformationProperty(
                                    priority=0,
                                    type="LOWERCASE"
                                )
                            ]
                        )
                    )
                )
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="AllowedRefererRule",
                sampled_requests_enabled=True
            )
        )

        web_acl.rules = [sepcific_referer_rule]

        return web_acl
        
    def _setup_hosted_zone(self):
        hosted_zone_id = ssm.StringParameter.from_string_parameter_attributes(
            self, "SyntrilloClinicRoute53HostedZoneId",
            parameter_name="/syntrillo-clinic/aws/route53/hosted_zone_id"
        ).string_value

        return route53.HostedZone.from_hosted_zone_attributes(
            self, "SyntrilloClinicBackendHostedZone",
            zone_name=f"{self.environment_name}.syntrillo-clinic-backend.com",
            hosted_zone_id=hosted_zone_id
        )

    def _setup_ssl_certificate(self):
        domain_name = f"{self.environment_name}.syntrillo-clinic-backend.com"
        api_domain_name = f"api.{self.environment_name}.syntrillo-clinic-backend.com"

        return acm.Certificate(
            self, "SyntrilloClinicBackendSSLCertificate",
            domain_name=domain_name,
            validation=acm.CertificateValidation.from_dns(self.hosted_zone),
            subject_alternative_names=[api_domain_name]
        )

    def _setup_log_destination(self):
        cloudwatch_logs_role = iam.Role(
            self, "APIGatewayCloudWatchLogsRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonAPIGatewayPushToCloudWatchLogs")
            ]
        )

        apigateway.CfnAccount(self, "APIGatewayAccountResource",
            cloud_watch_role_arn=cloudwatch_logs_role.role_arn
        )

        return logs.LogGroup(
            self, "IFrameGeneratorAPIAccessLogLogGroup",
            log_group_name="/aws/apigateway/IFrameGeneratorApiAccessLog"
        )
    
    def _setup_api_gateway(self):
        api_domain_name = f"api.{self.environment_name}.syntrillo-clinic-backend.com"

        api = apigateway.RestApi(
            self, "IFramGeneratorAPI",
            rest_api_name="IFramGeneratorAPI",
            domain_name=apigateway.DomainNameOptions(
                domain_name=api_domain_name,
                certificate=self.certificate
            ),
            deploy_options=apigateway.StageOptions(
                tracing_enabled=True,
                stage_name=self.environment_name,
                throttling_rate_limit=1000,
                throttling_burst_limit=500,
                access_log_destination=apigateway.LogGroupLogDestination(self.log_destination),
                logging_level=apigateway.MethodLoggingLevel.INFO,
            ),
            policy=self._resource_policy()
        )

        route53.ARecord(
            self, "SyntrilloCustomDomainARecord",
            zone=self.hosted_zone,
            record_name=api_domain_name,
            target=route53.RecordTarget.from_alias(
                route53_targets.ApiGateway(api)
            )
        )

        api.root.add_resource("ping").add_method("GET")

        return api

    def _resource_policy(self):
        allowed_ip_addresses = set(
            ip_info["ip"]
            for ip_info in self.environment_context["iframe_generator_api"]["allowed_api_adresses"]
        )

        allow_all_invokes_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.DENY,
            principals=[iam.AnyPrincipal()],
            actions=["execute-api:Invoke"],
            resources=["execute-api:/*/*/*"],
            conditions={
                "NotIpAddress": {
                    "aws:SourceIp": list(allowed_ip_addresses),
                }
            },
        )

        allowed_ips_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            principals=[iam.AnyPrincipal()],
            actions=["execute-api:Invoke"],
            resources=["execute-api:/*/*/*"]
        )

        return iam.PolicyDocument(statements=[
                allow_all_invokes_policy_statement, 
                allowed_ips_policy_statement
        ])