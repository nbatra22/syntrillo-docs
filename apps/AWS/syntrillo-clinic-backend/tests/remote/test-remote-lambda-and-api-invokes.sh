#!/bin/bash -e

# Load configuration from environment variables
FUNCTION_NAME="${FUNCTION_NAME:-IFrameGeneratorFunction}"
API_NAME="${API_NAME:-IFramGeneratorAPI}"

# Function to invoke a Lambda function
invoke_lambda_function() {
    local function_name="$1"
    local resource_path="$2"
    local payload="$3"

    local temp_file
    out_temp_file="/tmp/$(basename $resource_path).json"
    log_temp_file="/tmp/$(basename $resource_path).logs"

    aws lambda invoke \
        --cli-binary-format raw-in-base64-out \
        --function-name "$function_name" \
        --cli-binary-format raw-in-base64-out \
        --payload "$payload" \
        --log-type Tail \
        "$out_temp_file" > $log_temp_file
        
    local error_message
    error_message="$(jq '.errorMessage' "$out_temp_file")"

    local status_code
    status_code="$(jq '.statusCode' "$out_temp_file")"

    if [[ "$error_message" == "null" || "$status_code" == "200" ]]; then
        echo "Function $function_name ($resource_path) test passed"
    else
        echo "Function $function_name test failed"
        echo "status_code: "$status_code
        echo "error_message: "$error_message
        jq '.' "$out_temp_file"
        cat $log_temp_file |jq .LogResult | sed 's/^"//' | sed 's/"$//' | base64 --decode
        return 1
    fi
}

# Function to test an API Gateway endpoint
test_api_gateway_endpoint() {
    local resource_path="$1"
    local api_name="$2"
    local invoke_method="$3"

    local rest_api_id
    rest_api_id="$(aws apigateway get-rest-apis --query "items[?name=='$api_name'].id" --output text)"

    local resource_id
    resource_id="$(aws apigateway get-resources --rest-api-id "$rest_api_id" --query "items[?path=='$resource_path'].id" --output text)"

    local test_result
    test_result="$(aws apigateway test-invoke-method \
        --rest-api-id "$rest_api_id" \
        --resource-id "$resource_id" \
        --http-method $invoke_method \
        --path-with-query-string "$resource_path" \
        --body '')"

    local status
    status="$(echo "$test_result" | jq '.status')"

    if [[ "$status" == "200" ]]; then
        echo "API $api_name ($resource_path) test passed"
    else
        echo "API $api_name ($resource_path) test failed"
        echo "API OUTPUT"
        echo "$test_result" | jq '.'
        echo "LAMBDA OUTPUT"
        cat $log_temp_file |jq .LogResult | sed 's/^"//' | sed 's/"$//' | base64 --decode
        return 1
    fi
}


# # Test connectivity checks
# CONNECTIVITY_CHECK_PATHS=("/check_internet_ingress" "/check_internet_egress" "/check_mysql_database_access")
# for resource_path in "${CONNECTIVITY_CHECK_PATHS[@]}"; do
#     echo "---"$resource_path
#     invoke_lambda_function "CheckConnectivityFunction" "$resource_path" "{\"path\": \"$resource_path\"}"
#     test_api_gateway_endpoint "$resource_path" "CheckConnectivityAPI" "GET"
#     echo
# done

# # Test behavior checks
# BEHAVIOR_CHECK_PATHS=("/check_python_module_import")
# for resource_path in "${BEHAVIOR_CHECK_PATHS[@]}"; do
#     echo "---"$resource_path
#     invoke_lambda_function "CheckBehaviourFunction" "$resource_path" "{\"path\": \"$resource_path\"}"
#     test_api_gateway_endpoint "$resource_path" "CheckBehaviourAPI" "GET"
#     echo
# done

# Test iframe GET requests
IFRAME_GET_PATHS=("/" "/iframe_healthie_provider_tab")
for resource_path in "${IFRAME_GET_PATHS[@]}"; do
    echo "---"$resource_path
    invoke_lambda_function "$FUNCTION_NAME" "$resource_path" "{\"httpMethod\": \"GET\", \"path\": \"$resource_path\", \"queryStringParameters\": \"\"}"
    test_api_gateway_endpoint "$resource_path" "$API_NAME" "GET"
    echo
done

# # Test iframe POST requests
# IFRAME_POST_PATHS=("healthie/iframe_provider_tab/status")
# for resource_path in "${IFRAME_POST_PATHS[@]}"; do
#     echo "---"$resource_path
#     payload="$(cat event-samples/$(basename "$resource_path").json)"
#     invoke_lambda_function "$FUNCTION_NAME" "$resource_path" "$payload"
#     test_api_gateway_endpoint "$resource_path" "$API_NAME" "POST"
#     echo
# done
