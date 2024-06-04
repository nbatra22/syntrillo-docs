import aws_cdk as core
import aws_cdk.assertions as assertions

from syntrillo_clinic_backend.syntrillo_clinic_backend_stack import SyntrilloClinicBackendStack

# example tests. To run these tests, uncomment this file along with the example
# resource in syntrillo_clinic_backend/syntrillo_clinic_backend_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SyntrilloClinicBackendStack(app, "syntrillo-clinic-backend")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
