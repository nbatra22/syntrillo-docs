import aws_cdk as core
import aws_cdk.assertions as assertions

from syntrillo_clinic_backend.syntrillo_clinic_backend_stack import SyntrilloClinicBackendStack

import json

with open('cdk.context.json', 'r') as f:
    TEST_CONTEXT = json.load(f)

TEST_CONTEXT['environment']="sandbox"

def test_sqs_queue_created():
    app = core.App(context=TEST_CONTEXT)
    stack = SyntrilloClinicBackendStack(app, "syntrillo-clinic-backend")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
