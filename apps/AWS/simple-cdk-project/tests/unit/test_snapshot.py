import aws_cdk as core
import aws_cdk.assertions as assertions

from simple_cdk_project.simple_cdk_project_stack import SimpleCdkProjectStack

# 1. pip install syrupy (that will manage snapshot fixture in below function the argument
def test_snapshot(snapshot):
    app = core.App()
    stack = SimpleCdkProjectStack(app, "simple-cdk-project")
    template = assertions.Template.from_stack(stack)

    assert template.to_json() == snapshot # <= 2. need a snahot first : 'pytest --snapshot-update'

# 3. now, each time you run pytest, it will compare the synth result with the snapshot
# 4. you can get details of the differences with: 'pytest -vv'
# 5. when the difference is ok, you can create a new snaphot: 'pytest --snapshot-update'
# N.B the snapshot is stores under __snaphots__ in the unit test folder 