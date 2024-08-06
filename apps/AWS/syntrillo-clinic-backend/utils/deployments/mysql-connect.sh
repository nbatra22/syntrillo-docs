#!/bin/bash

if [ "$1" == "" ]; then
  echo "usage: $0 <environment>"
  echo "environments: sandbox, staging"
  exit
fi

ENVIRONMENT=$1
if [ "$ENVIRONMENT" == 'sandbox' ]; then
  SECRET_NAME='SyntrilloClinicBackendStack-oSWB6kcdQXhb'
fi

if [ "$ENVIRONMENT" == 'staging' ]; then
  SECRET_NAME='SyntrilloClinicBackendStack-vdxv5amcc1Vs'
fi

if [ "$(which jq)" == "" ]; then
  echo "!!!Please install jq"
  echo "example on ubuntu: sudo apt-get install jq"
  exit
fi

password=$(aws secretsmanager --profile syntrillo-clinic-$ENVIRONMENT \
		get-secret-value \
		--secret-id $SECRET_NAME \
		--query 'SecretString' \
		--output text | jq -r '.password')

echo '---'
echo "MYSQL DATABASE $ENVIRONMENT PASSWORD: $password"
echo "!!! N.B. : Using password is temporary, we should connect with IAM roles in the future"
echo '---'

echo "If the connection 'hangs', make sure that you have started the ssm session in the right environment"
echo "For example if you use did an ssm-start 'sanbox', and a mysql-connect 'staging' it will not work, and hang"

echo "---"
#password=$(aws secretsmanager --profile syntrillo-clinic-sandbox get-secret-value --secret-id SyntrilloClinicBackendStack-oSWB6kcdQXhb --query 'SecretString' --output text | jq -r '.password')
mysql -h 127.0.0.1 -P 3307 -u admin -p$password
if [ $? != 0 ]; then
  echo "!!!"
  echo "Make sure you have opened the sql-tunnel"
  echo "!!!"
fi
