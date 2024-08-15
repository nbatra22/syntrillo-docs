#!/bin/bash

# Set the AWS profile name (optional)
export AWS_PROFILE=syntrillo-clinic-prod-deployment

# Set the conformance pack name
CONFORMANCE_PACK_NAME="HIPAA-Conformance-Pack"

# Initialize variables for pagination
NEXT_TOKEN=""
RULES=()

# Iterate through pages
while true; do
    # Call describe-conformance-pack-compliance
    RESPONSE=$(aws configservice describe-conformance-pack-compliance \
        --conformance-pack-name "$CONFORMANCE_PACK_NAME" \
        --next-token "$NEXT_TOKEN" \
        --output json)

    # Extract all rules from the response
    RULES+=($(echo "$RESPONSE" | jq -r '.ConformancePackRuleComplianceList[] | "\(.ConfigRuleName);\(.ComplianceType)"'))

    # Check if there's a next token
    NEXT_TOKEN=$(echo "$RESPONSE" | jq -r '.NextToken // ""')
    if [ -z "$NEXT_TOKEN" ]; then
        break
    fi
done

# Print all rules and their compliance status
for RULE in "${RULES[@]}"; do
    echo "$RULE"
done
