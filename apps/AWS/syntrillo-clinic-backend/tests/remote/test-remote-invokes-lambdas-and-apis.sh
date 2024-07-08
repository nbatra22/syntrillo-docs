#!/bin/bash -e

source ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/tests/remote/_invoke-lambdas-and-api-functions.sh

# Test iframe GET requests
IFRAME_GET_PATHS=("/" "/iframe_healthie_provider_tab")
for resource_path in "${IFRAME_GET_PATHS[@]}"; do
    echo "---"$resource_path
    invoke_lambda_function "$FUNCTION_NAME" "$resource_path" "{\"httpMethod\": \"GET\", \"path\": \"$resource_path\", \"queryStringParameters\": \"\"}"
    test_api_gateway_endpoint "$resource_path" "$API_NAME" "GET"
    echo
done

# Test iframe POST requests
IFRAME_POST_PATHS=("/healthie/iframe_provider_tab/devices")
for resource_path in "${IFRAME_POST_PATHS[@]}"; do
    echo "---"$resource_path
    payload="$(cat ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/utils/event-samples/$(basename "$resource_path").json)"
    invoke_lambda_function "$FUNCTION_NAME" "$resource_path" "$payload"
    test_api_gateway_endpoint "$resource_path" "$API_NAME" "POST"
    echo
done
