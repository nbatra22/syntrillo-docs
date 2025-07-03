#!/bin/bash

# Script to create a Cognito user without forcing password change
# Usage: ./create-cognito-user.sh <user-pool-id> <username> <password> <email> [region]

set -e

# Function to display usage
usage() {
    echo "Usage: $0 <environment> <email>"
    echo "Example: $0 [staging|prod] john.doe@example.com"
    exit 1
}

# Check if required parameters are provided
if [ $# -lt 2 ]; then
    echo "Error: Missing required parameters"
    usage
fi

if [ "$1" != "staging" ] && [ "$1" != "prod" ]; then
    echo "Error: Invalid environment. Must be 'staging' or 'prod'."
    usage
fi

USERNAME="$2"
EMAIL="$2"
# Generate a random 8-character password at least one lowercase, at least one upper case, at least one numbers and one special characters
PASSWORD=$(echo "$(tr -dc 'a-z' < /dev/urandom | head -c1)$(tr -dc 'A-Z' < /dev/urandom | head -c1)$(tr -dc '0-9' < /dev/urandom | head -c1)$(tr -dc '!@#$%^&*' < /dev/urandom | head -c1)$(tr -dc 'a-zA-Z0-9!@#$%^&*' < /dev/urandom | head -c4)" | fold -w1 | shuf | tr -d '\n')

if [ "$1" == "prod" ]; then
    PROFILE="syntrillo-clinic-prod"
    USER_POOL_ID="us-east-1_vcbX8U5g2"
fi

if [ "$1" == "staging" ]; then
    PROFILE="syntrillo-clinic-staging"
    USER_POOL_ID="us-east-1_pIEf3KLMj"
fi

REGION="us-east-1"

echo "Creating Cognito user..."
echo "User Pool ID: $USER_POOL_ID"
echo "Username: $USERNAME"
echo "Email: $EMAIL"
echo "Region: $REGION"

# Create the user
echo "Step 1: Creating user in Cognito User Pool..."
aws cognito-idp admin-create-user --profile $PROFILE \
    --user-pool-id "$USER_POOL_ID" \
    --username "$USERNAME" \
    --user-attributes Name=email,Value="$EMAIL" Name=email_verified,Value=true \
    --temporary-password "$PASSWORD" \
    --message-action SUPPRESS \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✓ User created successfully"
else
    echo "✗ Failed to create user"
    exit 1
fi

# Set permanent password
echo "Step 2: Setting permanent password..."
aws cognito-idp admin-set-user-password --profile $PROFILE \
    --user-pool-id "$USER_POOL_ID" \
    --username "$USERNAME" \
    --password "$PASSWORD" \
    --permanent \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✓ Password set as permanent"
else
    echo "✗ Failed to set permanent password"
    exit 1
fi

# Confirm the user (mark as verified) - only if not already confirmed
echo "Step 3: Checking and confirming user account..."
USER_STATUS=$(aws cognito-idp admin-get-user --profile $PROFILE \
    --user-pool-id "$USER_POOL_ID" \
    --username "$USERNAME" \
    --region "$REGION" \
    --query 'UserStatus' --output text 2>/dev/null)

if [ "$USER_STATUS" = "CONFIRMED" ]; then
    echo "✓ User account already confirmed"
else
    aws cognito-idp admin-confirm-sign-up --profile $PROFILE \
        --user-pool-id "$USER_POOL_ID" \
        --username "$USERNAME" \
        --region "$REGION"
    
    if [ $? -eq 0 ]; then
        echo "✓ User account confirmed"
    else
        echo "✗ Failed to confirm user account"
        exit 1
    fi
fi

echo ""
echo "🎉 User '$USERNAME' has been successfully created!"
echo "   - Email: $EMAIL"
echo "   - Password: Set as permanent (no forced change required)"
echo "   - Status: Confirmed and ready to use"
