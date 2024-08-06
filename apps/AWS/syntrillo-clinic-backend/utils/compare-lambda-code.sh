#!/bin/bash

# Set the Lambda function name
FUNCTION_NAME="IFrameGeneratorFunction"

# Download the remote function code
REMOTE_CODE_URL=$(aws lambda get-function --function-name "$FUNCTION_NAME" --query 'Code.Location' --output text)
curl -L -o remote_code.zip "$REMOTE_CODE_URL"

# Extract the remote function code
unzip -q remote_code.zip -d remote_code

# Compare the remote code with the local code
diff -r remote_code/ ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/lambda-functions/iframe-generator-function/

# Clean up
rm -rf remote_code.zip remote_code

