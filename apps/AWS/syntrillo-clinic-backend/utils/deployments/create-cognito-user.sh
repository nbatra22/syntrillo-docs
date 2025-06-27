#!/bin/bash

# Script to create a Cognito user without forcing password change
# Usage: ./create-cognito-user.sh <user-pool-id> <username> <password> <email> [region]

set -e

# Function to display usage
usage() {
    echo "Usage: $0 <user-pool-id> <username> <password> <email> [region]"
    echo "Example: $0 us-east-1_ABC123DEF john.doe MySecurePass123! john.doe@example.com us-east-1"
    exit 1
}

# Check if required parameters are provided
if [ $# -lt 4 ]; then
    echo "Error: Missing required parameters"
    usage
fi

PROFILE="syntrillo-clinic-staging"
USER_POOL_ID="$1"
USERNAME="$2"
PASSWORD="$3"
EMAIL="$4"
REGION="${5:-us-east-1}"  # Default to us-east-1 if not specified

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

# Confirm the user (mark as verified)
echo "Step 3: Confirming user account..."
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

echo ""
echo "🎉 User '$USERNAME' has been successfully created!"
echo "   - Email: $EMAIL"
echo "   - Password: Set as permanent (no forced change required)"
echo "   - Status: Confirmed and ready to use"
