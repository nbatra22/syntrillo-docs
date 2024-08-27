#!/bin/bash

# make sure we are in the directory of this script
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")";

# go to the root of the CDK app
#  : ./apps/AWS/syntrillo-clinic-backend
cd ../../

cdk deploy --profile syntrillo-clinic-staging --role-arn 'arn:aws:iam::021891579520:role/cdk-prodlike-cfn-exec-role' --context 'environment=staging' $@
