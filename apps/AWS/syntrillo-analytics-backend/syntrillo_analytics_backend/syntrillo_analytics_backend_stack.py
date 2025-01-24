from aws_cdk import (
    Stack,
)
from constructs import Construct

from syntrillo_analytics_backend.substacks.network_stack import NetworkStack
from syntrillo_analytics_backend.substacks.ingestion_stack import IngestionStack
from syntrillo_analytics_backend.substacks.storage_stack import StorageStack
from syntrillo_analytics_backend.substacks.query_stack import QueryStack

import json

class SyntrilloAnalyticsBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.aws_environment = self.node.try_get_context("environment")
        if self.aws_environment == None:
            self.aws_environment = "sandbox"
        
        self.environment_context = self.node.try_get_context(self.aws_environment)

        # self.termination_protection = self.environment_context["stacks-termination-protection"]

        print("--------------------------------------")
        print(f"SyntrilloAnalyticsBackendStack AWS Environement : <{self.aws_environment}>")
        print(f"")
        print("--------------------------------------")
        print(f"SyntrilloAnalyticsBackendStack AWS Environment Context :")
        print(json.dumps(self.environment_context, indent=4))
        print("--------------------------------------")


        network_stack = NetworkStack(
            self, "NetworkStack", 
            environment_context=self.environment_context,
        )

        storage_stack = StorageStack(
            self, "StorageStack", 
            environment_context=self.environment_context,
        )

        ingestion_stack = IngestionStack(
            self, "IngestionStack", 
            environment_context=self.environment_context,
            network = network_stack,
            storage = storage_stack
        )

        query_stack = QueryStack(
            self, "QueryStack", 
            environment_context=self.environment_context,
        )        