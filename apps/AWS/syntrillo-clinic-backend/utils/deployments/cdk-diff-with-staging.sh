#!/bin/bash

# make sure we are in the directory of this script
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")";

# go to the root of the CDK app
#  : ./apps/AWS/syntrillo-clinic-backend
cd ../../

cdk diff --profile syntrillo-clinic-staging --context 'environment=staging' $@
