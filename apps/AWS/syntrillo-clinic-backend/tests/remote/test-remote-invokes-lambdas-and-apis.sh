#!/bin/bash -e

source ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/tests/remote/_invoke-lambdas-and-api-functions.sh

# Test iframe GET requests
IFRAME_GET_PATHS=(\
    "/" \
    "/iframe_healthie_provider_tab" \
)
for resource_path in "${IFRAME_GET_PATHS[@]}"; do
    echo "---"$resource_path
    payload="{\"httpMethod\": \"GET\", \"path\": \"$resource_path\", \"queryStringParameters\": \"\"}"
    body="$(cat ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/utils/api-body-and-headers-samples/$(basename "$resource_path").body)"
    headers="$(cat ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/utils/api-body-and-headers-samples/$(basename "$resource_path").headers)"
    invoke_lambda_function "$FUNCTION_NAME" "$resource_path" "$payload"
    invoke_api_resource "$resource_path" "$API_NAME" "GET" "$headers" "$body"
    echo
done

# Test iframe POST requests
IFRAME_POST_PATHS=(\
    "/healthie/iframe_provider_tab/status" \
    "/healthie/iframe_provider_tab/devices" \
    "/healthie/iframe_provider_tab/onboarding" \
    "/healthie/iframe_provider_tab/care_plan" \
    "/healthie/iframe_provider_tab/cdss" \
    "/healthie/iframe_provider_tab/system" \
    "/healthie/iframe_provider_tab/system_devices"\
)
for resource_path in "${IFRAME_POST_PATHS[@]}"; do
    echo "---"$resource_path
    payload="$(cat ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/utils/lambda-event-samples/$(basename "$resource_path").json)"
    body="$(cat ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/utils/api-body-and-headers-samples/$(basename "$resource_path").body)"
    headers="$(cat ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/utils/api-body-and-headers-samples/$(basename "$resource_path").headers)"
    invoke_lambda_function "$FUNCTION_NAME" "$resource_path" "$payload"
    invoke_api_resource "$resource_path" "$API_NAME" "POST" "$headers" "$body" 
    call_api_enpoint "$resource_path" "$API_NAME" "POST" "$headers" "$body"
    echo
done


