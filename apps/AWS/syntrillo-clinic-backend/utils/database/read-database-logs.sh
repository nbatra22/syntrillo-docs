#!/bin/bash

if [ "$1" == "" ]; then
  echo "usage: $0 <environment>"
  echo "environments: sandbox, staging"
  exit
fi

ENVIRONMENT=$1
if [ "$ENVIRONMENT" == 'sandbox' ]; then
  RDS_INSTANCE_NAME="syntrilloclinicbackendsta-mysqldatabasefromsnapsho-pgfocymgbys3"
fi

if [ "$ENVIRONMENT" == 'staging' ]; then
  RDS_INSTANCE_NAME="syntrilloclinicbackendsta-mysqldatabasefromsnapsho-saiukm5mugdm"
fi

PROFILE="syntrillo-clinic-$ENVIRONMENT"

# Get the list of log files
LOG_FILES=$(aws rds --profile $PROFILE describe-db-log-files --db-instance-identifier "$RDS_INSTANCE_NAME" --query "DescribeDBLogFiles[?starts_with(LogFileName, 'error/mysql-error-running.log.2024-09-19')].LogFileName" --output text)

echo $LOG_FILES
# Loop through the log files and download those matching the pattern
for LOG_FILE in $LOG_FILES; do
    echo "Downloading log file: $LOG_FILE"
    aws rds download-db-log-file-portion \
	--profile $PROFILE \
        --db-instance-identifier "$RDS_INSTANCE_NAME" \
        --log-file-name "$LOG_FILE" \
        --output text # > "${LOG_FILE}.txt"
done
