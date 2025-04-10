#!/bin/bash

# make sure we are in the directory of this script
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")";

# go to the root of the CDK app
#  : ./apps/AWS/syntrillo-clinic-backend
cd ../../

PROFILE="--profile syntrillo-clinic-prod-deployment"
if [ -n "$CODEBUILD_BUILD_ID" ]; then
    PROFILE=""
fi

cdk diff $PROFILE --context environment='prod' $@ 
