#!/usr/bin/env python3
import os

import aws_cdk as cdk

from simple_cdk_stacks.simple_api_lambda_stack import SimpleApiLambdaStack
from simple_cdk_stacks.simple_rds_s3_export_stack import SimpleRDSS3ExportStack
from simple_cdk_stacks.simple_http_resolver_stack import SimpleHttpResolverStack
from simple_cdk_stacks.simple_flask_wsgi_stack import SimpleFlaskWsgiStack
from simple_cdk_stacks.simple_download_stack import SimpleDownloadStack

app = cdk.App()
SimpleApiLambdaStack(app, "SimpleApiLambdaStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

SimpleRDSS3ExportStack(app, "SimpleRDSS3ExportStack")
SimpleHttpResolverStack(app, "SimpleHttpResolverStack")
SimpleFlaskWsgiStack(app, "SimpleFlaskWsgiStack")
SimpleDownloadStack(app, "SimpleDownloadStack")

app.synth()
