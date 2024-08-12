import aws_cdk as core
import aws_cdk.assertions as assertions

from simple_cdk_stacks.simple_cdk_stacks_stack import SimpleCdkStacksStack

# example tests. To run these tests, uncomment this file along with the example
# resource in simple_cdk_stacks/simple_cdk_stacks_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SimpleCdkStacksStack(app, "simple-cdk-stacks")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
