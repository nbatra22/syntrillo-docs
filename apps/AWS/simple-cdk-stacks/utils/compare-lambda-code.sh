#!/bin/bash

# Set the Lambda function name
FUNCTION_NAME="SimpleFlaskWsgiStack-SimpleLambdaFunctionD523701A-MBwzX0TJaG2b"

# Download the remote function code
REMOTE_CODE_URL=$(aws lambda --profile syntrillo-clinic-sandbox get-function --function-name "$FUNCTION_NAME" --query 'Code.Location' --output text)
curl -L -o remote_code.zip "$REMOTE_CODE_URL"

# Extract the remote function code
unzip -q remote_code.zip -d remote_code

# Compare the remote code with the local code
diff -r remote_code/ ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/lambda-functions/servers/iframe-generator-function/ --exclude "*.pyc" --exclude "__init__.py" --exclude "__pycache__" 

# Clean up
rm -rf remote_code.zip remote_code


