import aws_cdk as core
import aws_cdk.assertions as assertions

from syntrillo_genai_backend_sandbox.syntrillo_genai_backend_sandbox_stack import SyntrilloGenaiBackendSandboxStack

# example tests. To run these tests, uncomment this file along with the example
# resource in syntrillo_genai_backend_sandbox/syntrillo_genai_backend_sandbox_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SyntrilloGenaiBackendSandboxStack(app, "syntrillo-genai-backend-sandbox")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
