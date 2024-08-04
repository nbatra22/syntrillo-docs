import aws_cdk as core
import aws_cdk.assertions as assertions

from syntrillo_clinic_backend.syntrillo_clinic_backend_stack import SyntrilloClinicBackendStack

import json

with open('cdk.context.json', 'r') as f:
    TEST_CONTEXT = json.load(f)

TEST_CONTEXT['environment']="sandbox"

app = core.App(context=TEST_CONTEXT)
syntrillo_clinic_backend_stack = SyntrilloClinicBackendStack(app, "syntrillo-clinic-backend")

def test_snapshot_syntrillo_clinic_backend_stack(snapshot):
    template = assertions.Template.from_stack(syntrillo_clinic_backend_stack)
    assert template.to_json() == snapshot

def test_snapshot_network_stack(snapshot):
    stack = syntrillo_clinic_backend_stack.network
    template = assertions.Template.from_stack(stack)
    assert template.to_json() == snapshot

def test_snapshot_database_stack(snapshot):
    stack = syntrillo_clinic_backend_stack.database
    template = assertions.Template.from_stack(stack)
    assert template.to_json() == snapshot
  
def test_snapshot_storage_stack(snapshot):
    stack = syntrillo_clinic_backend_stack.storage
    template = assertions.Template.from_stack(stack)
    assert template.to_json() == snapshot

def test_snapshot_secrets_stack(snapshot):
    stack = syntrillo_clinic_backend_stack.secrets
    template = assertions.Template.from_stack(stack)
    assert template.to_json() == snapshot

def test_snapshot_servers_stack(snapshot):
    stack = syntrillo_clinic_backend_stack.servers
    template = assertions.Template.from_stack(stack)
    assert template.to_json() == snapshot

def test_snapshot_schedule_tasks(snapshot):
    stack = syntrillo_clinic_backend_stack.scheduled_tasks
    template = assertions.Template.from_stack(stack)
    assert template.to_json() == snapshot