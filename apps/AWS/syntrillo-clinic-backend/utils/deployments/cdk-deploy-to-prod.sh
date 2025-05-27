#!/bin/bash

# ----------------------------------------------------------------------------------
# Deploy from codebuild
# ----------------------------------------------------------------------------------

if [ -n "$CODEBUILD_BUILD_ID" ]; then
  # make sure we are in the directory of this script
  cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")";

  # go to the root of the CDK app
  #  : ./apps/AWS/syntrillo-clinic-backend
  cd ../../

  cdk deploy --context environment='prod' $@ 
  exit
fi

# ----------------------------------------------------------------------------------
# Deploy from desktop
# ----------------------------------------------------------------------------------

if [ "$1" == "" ]; then
 cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend
 cdk ls --profile syntrillo-clinic-prod-deployment --context environment='prod'
 exit
fi

read -rp "!!! You are deploying to PRODUCTION, are you sure (Yes/no)? " confirmation

if [ "$confirmation" == "Yes" ]; then

  echo "make DIFF between staging and prod permissions"
  ./diff-deployment-staging-prod-policy.sh
  read -rp "!!! You are happy with the permissions (Yes/no)? " confirmation

  if [ "$confirmation" == "Yes" ]; then
    cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend
    echo "Make DIFF with new revision..."
    cdk diff --profile syntrillo-clinic-prod-deployment --context environment='prod' $@ 
    read -rp "!!! Are you happy with what will be deployed (Yes/no)? " confirmation
    if [ "$confirmation" == "Yes" ]; then
      echo "Start PROD deployment..."
      cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend
      cdk deploy --profile syntrillo-clinic-prod-deployment --context environment='prod' $@ 
    else
      echo "Aborted"
    fi
  else
    echo "Aborted"
  fi

else
  echo "Aborted"
fi

