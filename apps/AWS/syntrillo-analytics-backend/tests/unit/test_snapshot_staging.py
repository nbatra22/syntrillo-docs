import aws_cdk as core
import aws_cdk.assertions as assertions

from syntrillo_analytics_backend.syntrillo_analytics_backend_stack import SyntrilloAnalyticsBackendStack

import json

with open('cdk.context.json', 'r') as f:
    TEST_CONTEXT = json.load(f)

TEST_CONTEXT['environment']="staging"

app = core.App(context=TEST_CONTEXT)
syntrillo_analytics_backend_stack = SyntrilloAnalyticsBackendStack(app, "syntrillo-analytics-backend")

def test_snapshot_syntrillo_analytics_backend_stack(snapshot):
    template = assertions.Template.from_stack(syntrillo_analytics_backend_stack)
    assert template.to_json() == snapshot

def test_snapshot_network_stack(snapshot):
    stack = syntrillo_analytics_backend_stack.network
    template = assertions.Template.from_stack(stack)
    assert template.to_json() == snapshot

def test_snapshot_database_stack(snapshot):
    stack = syntrillo_analytics_backend_stack.storage
    template = assertions.Template.from_stack(stack)
    assert template.to_json() == snapshot
  
def test_snapshot_storage_stack(snapshot):
    stack = syntrillo_analytics_backend_stack.ingestion
    template = assertions.Template.from_stack(stack)
    assert template.to_json() == snapshot

def test_snapshot_secrets_stack(snapshot):
    stack = syntrillo_analytics_backend_stack.query
    template = assertions.Template.from_stack(stack)
    assert template.to_json() == snapshot