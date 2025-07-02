#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <environment>"
  echo "Environments: sandbox, staging, prod-deployment"
  exit
fi

ENVIRONMENT=$1

# Set the Lambda function name
FUNCTION_NAME="IFrameGeneratorFunction"

echo "-------------------------------"
echo "DIFF WITH $FUNCTION_NAME ($ENVIRONMENT)"
echo "-------------------------------"

# Download the remote function code
REMOTE_CODE_URL=$(aws lambda --profile syntrillo-clinic-$ENVIRONMENT get-function --function-name "$FUNCTION_NAME" --query 'Code.Location' --output text)
curl -L -o remote_code.zip "$REMOTE_CODE_URL"

# Extract the remote function code
unzip -q remote_code.zip -d remote_code

# Compare the remote code with the local code
diff -r remote_code/ ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/lambda-functions/servers/iframe-generator-function/ --exclude "*.pyc" --exclude "__init__.py" --exclude "__pycache__" 

# Clean up
rm -rf remote_code.zip remote_code


# Set the Lambda function name
FUNCTION_NAME="RemoteMonitoringDataSyncFunction"

echo "-------------------------------"
echo "DIFF WITH $FUNCTION_NAME ($ENVIRONMENT)"
echo "-------------------------------"

# Download the remote function code
REMOTE_CODE_URL=$(aws lambda --profile syntrillo-clinic-$ENVIRONMENT get-function --function-name "$FUNCTION_NAME" --query 'Code.Location' --output text)
curl -L -o remote_code.zip "$REMOTE_CODE_URL"

# Extract the remote function code
unzip -q remote_code.zip -d remote_code

# Compare the remote code with the local code
diff -r remote_code/ ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/lambda-functions/tasks/remote-monitoring-data-sync-function/ --exclude "*.pyc" --exclude "__init__.py" --exclude "__pycache__" 

# Clean up
rm -rf remote_code.zip remote_code
