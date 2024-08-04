import aws_cdk as core
import aws_cdk.assertions as assertions

from simple_cdk_stack.simple_cdk_stack_stack import SimpleCdkStackStack

# example tests. To run these tests, uncomment this file along with the example
# resource in simple_cdk_stack/simple_cdk_stack_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SimpleCdkStackStack(app, "simple-cdk-stack")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
