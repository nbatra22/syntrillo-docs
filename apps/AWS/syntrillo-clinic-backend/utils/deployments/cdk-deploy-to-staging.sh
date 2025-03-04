#!/bin/bash

# make sure we are in the directory of this script
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")";

# go to the root of the CDK app
#  : ./apps/AWS/syntrillo-clinic-backend
cd ../../

if [ "$1" == "--admin" ]; then
  echo "deploy with ADMIN permissions"
  ROLE_ARN=""
  shift
else
  ROLE_ARN="--role-arn arn:aws:iam::021891579520:role/cdk-prodlike-cfn-exec-role"	
fi

PROFILE="--profile syntrillo-clinic-staging-deployment"
if [ -n "$CODEBUILD_BUILD_ID" ]; then
    PROFILE=""
fi

cdk deploy $PROFILE $ROLE_ARN --context 'environment=staging' $@
