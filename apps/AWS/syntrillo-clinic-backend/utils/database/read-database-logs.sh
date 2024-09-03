#!/bin/bash

# Set the RDS instance identifier
# RDS_INSTANCE_NAME="syntrilloclinicbackendsta-mysqldatabasefromsnapsho-pgfocymgbys3"
# RDS_INSTANCE_NAME="syntrilloclinicbackendsta-mysqldatabasefromsnapsho-kiqcjpf09qy6"
RDS_INSTANCE_NAME="syntrilloclinicbackendsta-mysqldatabasefromsnapsho-pgfocymgbys3"

ENVIRONMENT="syntrillo-clinic-sandbox" #prod-deployment"

# Get the list of log files
LOG_FILES=$(aws rds --profile $ENVIRONMENT describe-db-log-files --db-instance-identifier "$RDS_INSTANCE_NAME" --query "DescribeDBLogFiles[?starts_with(LogFileName, 'error/mysql-error-running.log.2024-08-20')].LogFileName" --output text)

echo $LOG_FILES
# Loop through the log files and download those matching the pattern
for LOG_FILE in $LOG_FILES; do
    echo "Downloading log file: $LOG_FILE"
    aws rds download-db-log-file-portion \
        --db-instance-identifier "$RDS_INSTANCE_NAME" \
        --log-file-name "$LOG_FILE" \
        --output text # > "${LOG_FILE}.txt"
done
