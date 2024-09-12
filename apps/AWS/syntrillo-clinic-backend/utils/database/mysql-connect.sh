#!/bin/bash

if [ "$1" == "" ]; then
  echo "usage: $0 <environment>"
  echo "environments: sandbox, staging"
  exit
fi

ENVIRONMENT=$1
if [ "$ENVIRONMENT" == 'sandbox' ]; then
  SECRET_NAME='DatabaseAdminSecrets4B85717-Tqw6AojniUp9'
fi

if [ "$ENVIRONMENT" == 'staging' ]; then
  SECRET_NAME='DatabaseAdminSecrets4B85717-uGKLcnzcSCua'
fi

if [ "$(which jq)" == "" ]; then
  echo "!!!Please install jq"
  echo "example on ubuntu: sudo apt-get install jq"
  exit
fi

username=$(aws secretsmanager --profile syntrillo-clinic-$ENVIRONMENT \
		get-secret-value \
		--secret-id $SECRET_NAME \
		--query 'SecretString' \
		--output text | jq -r '.username')

password=$(aws secretsmanager --profile syntrillo-clinic-$ENVIRONMENT \
		get-secret-value \
		--secret-id $SECRET_NAME \
		--query 'SecretString' \
		--output text | jq -r '.password')

local_port='3307'

echo '---'
echo "ENVIRONEMENT: $ENVIRONMENT"
echo "MYSQL DATABASE $ENVIRONMENT USER NAME: $username"
echo "MYSQL DATABASE $ENVIRONMENT PASSWORD: $password"
echo "!!! N.B. : Using password is temporary, we should connect with IAM roles in the future"
echo '---'

echo "If the connection 'hangs', make sure that you have started the ssm session in the right environment"
echo "For example if you use did an ssm-start 'sanbox', and a mysql-connect 'staging' it will not work, and hang"

SSL_OPTION_FOR_MARIA_DB="--ssl"
mysql --version | grep -q 'Ver 8' && SSL_OPTION_FOR_MARIA_DB=""

echo "---"
mysql -h 127.0.0.1 -P $local_port -u $username -p$password $SSL_OPTION_FOR_MARIA_DB
if [ $? != 0 ]; then
  echo "!!!"
  echo "Make sure you have opened the sql-tunnel"
  echo "!!!"
fi
