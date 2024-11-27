#!/bin/bash

# make sure we are in the directory of this script
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")";

# go to the root of the CDK app
#  : ./apps/AWS/syntrillo-clinic-backend
cd ../../

if [ "$1" == "admin" ]; then
  echo "deploy with ADMIN permissions"
  role_arn=""
  shift
else
  role_arn="--role-arn arn:aws:iam::021891579520:role/cdk-prodlike-cfn-exec-role"	
fi

cdk deploy --profile syntrillo-clinic-staging-deployment $role_arn --context 'environment=staging' $@
