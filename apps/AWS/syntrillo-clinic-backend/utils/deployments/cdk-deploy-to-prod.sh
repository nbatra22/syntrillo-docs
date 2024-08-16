#!/bin/bash

if [ "$1" == "" ]; then
 cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend
 cdk ls --profile syntrillo-clinic-prod-deployment --context environment='prod'
 exit
fi

read -rp "!!! You are deploying to PRODUCTION, are you sure (Yes/no)? " confirmation

if [ "$confirmation" == "Yes" ]; then
  cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend
  echo "Make DIFF with new revision..."
  cdk diff --profile syntrillo-clinic-prod-deployment --context environment='prod' $@ 
  read -rp "!!! Are you happy with what will be deployed (Yes/no)? " confirmation
  if [ "$confirmation" == "Yes" ]; then
    echo "Start PROD deployment..."
    cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend
    cdk deploy --profile syntrillo-clinic-prod-deployment --context environment='prod' $@ 
  fi
else
  echo "Aborted"
fi

