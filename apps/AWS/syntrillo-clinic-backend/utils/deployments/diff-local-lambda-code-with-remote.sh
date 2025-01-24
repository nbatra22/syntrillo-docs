#!/bin/bash

if [ "$1" == "" ]; then
  echo "Usage: $0 <environment>"
  echo "Environments: sandbox, staging, prod"
  exit
fi

ENVIRONMENT=$1

cd ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend
cdk diff --profile syntrillo-clinic-$ENVIRONMENT --context environment="$ENVIRONMENT" 2>&1 | tee /tmp/cdk-diff.txt

cat /tmp/cdk-diff.txt |grep 'AWS::Lambda::Function' | cut -d'/' -f2 | tee /tmp/functions.txt
cat /tmp/cdk-diff.txt | grep '\[+\] [0-9a-z]*\.zip$' | grep -o "[0-9a-z]\{64\}" | tee /tmp/assets.txt

asset_row_number=1
functions=$(cat /tmp/functions.txt)

if [ "$functions" == "" ]; then
  echo "No changes detected"
  exit
fi

for function_name in $functions; do
  asset_ref=$(sed -n "${asset_row_number}p" /tmp/assets.txt)
  asset_folder="asset.$asset_ref"
  echo $asset_folder

  echo "-------------------------------"
  echo "COMPARING..."
  echo "function name: $function_name"
  echo "asset folder: $asset_folder"
  echo "-------------------------------"

  REMOTE_CODE_URL=$(aws lambda get-function --profile syntrillo-clinic-$ENVIRONMENT --function-name $function_name --query 'Code.Location' --output text)
  curl -L -o /tmp/remote_code.zip "$REMOTE_CODE_URL"
  unzip -q /tmp/remote_code.zip -d /tmp/remote_code

  diff -r /tmp/remote_code/ cdk.out/$asset_folder/ || true

  rm -r /tmp/remote* 

  let asset_row_number=$asset_row_number+1
done
rm /tmp/functions.txt /tmp/assets.txt
cd -

exit
# --------------------------------------------------------------------------

# ENVIRONMENT=$1

# # Set the Lambda function name
# FUNCTION_NAME="IFrameGeneratorFunction"

# echo "-------------------------------"
# echo "DIFF WITH $FUNCTION_NAME ($ENVIRONMENT)"
# echo "-------------------------------"

# # Download the remote function code
# REMOTE_CODE_URL=$(aws lambda --profile syntrillo-clinic-$ENVIRONMENT get-function --function-name "$FUNCTION_NAME" --query 'Code.Location' --output text)
# curl -L -o remote_code.zip "$REMOTE_CODE_URL"

# # Extract the remote function code
# unzip -q remote_code.zip -d remote_code

# # Compare the remote code with the local code
# diff -r remote_code/ ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/lambda-functions/iframe-generator-function/ --exclude "*.pyc" --exclude "__init__.py" --exclude "__pycache__" 

# # Clean up
# rm -rf remote_code.zip remote_code


# # Set the Lambda function name
# FUNCTION_NAME="RemoteMonitoringDataSyncFunction"

# echo "-------------------------------"
# echo "DIFF WITH $FUNCTION_NAME ($ENVIRONMENT)"
# echo "-------------------------------"

# # Download the remote function code
# REMOTE_CODE_URL=$(aws lambda --profile syntrillo-clinic-$ENVIRONMENT get-function --function-name "$FUNCTION_NAME" --query 'Code.Location' --output text)
# curl -L -o remote_code.zip "$REMOTE_CODE_URL"

# # Extract the remote function code
# unzip -q remote_code.zip -d remote_code

# # Compare the remote code with the local code
# diff -r remote_code/ ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/lambda-functions/remote-monitoring-data-sync-function/ --exclude "*.pyc" --exclude "__init__.py" --exclude "__pycache__" 

# # Clean up
# rm -rf remote_code.zip remote_code
