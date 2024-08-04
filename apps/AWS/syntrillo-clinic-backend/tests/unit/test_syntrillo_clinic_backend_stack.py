import aws_cdk as core
import aws_cdk.assertions as assertions

from syntrillo_clinic_backend.syntrillo_clinic_backend_stack import SyntrilloClinicBackendStack

TEST_CONTEXT = {
  "sandbox": {
    "iframe_generator_function": {
      "provisioned_concurrency_executions": 0
    }
  }
}

def test_sqs_queue_created():
    app = core.App(context=TEST_CONTEXT)
    stack = SyntrilloClinicBackendStack(app, "syntrillo-clinic-backend")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
