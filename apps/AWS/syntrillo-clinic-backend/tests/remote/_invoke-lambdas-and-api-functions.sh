# Load configuration from environment variables
FUNCTION_NAME="${FUNCTION_NAME:-IFrameGeneratorFunction}"
API_NAME="${API_NAME:-IFramGeneratorAPI}"

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

invoke_api_resource() {
    local resource_path="$1"
    local api_name="$2"
    local invoke_method="$3"
    local headers="$4"
    local body="$5"
    
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
        --headers "$headers" \
        --body "$body")"

    local status
    status="$(echo "$test_result" | jq '.status')"

    if [[ "$status" == "200" ]]; then
        echo "API $api_name ($resource_path) test passed"
    else
        echo "API $api_name ($resource_path) test failed ($status)"
        
        echo "INVOKE:"

        echo aws apigateway get-rest-apis --query "items[?name=='$api_name'].id" --output text
        echo aws apigateway get-resources --rest-api-id "$rest_api_id" --query "\"items[?path=='$resource_path'].id\"" --output text

        echo aws apigateway test-invoke-method \
        --rest-api-id "$rest_api_id" \
        --resource-id "$resource_id" \
        --http-method $invoke_method \
        --path-with-query-string "$resource_path" \
        --headers "$headers" \
        --body "$body"

        echo "API OUTPUT:"
        echo "$test_result" | jq '.'

        echo "LAMBDA OUTPUT:"
        cat $log_temp_file |jq .LogResult | sed 's/^"//' | sed 's/"$//' | base64 --decode

        return 1
    fi
}

call_api_enpoint() {
    local resource_path="$1"
    local api_name="$2"
    local invoke_method="$3"
    local headers="$4"
    local body="$5"
    
    api_endpoint="https://api.sandbox.syntrillo-clinic-backend.com"$resource_path

    local test_result
    test_result="$(curl -X "$invoke_method" "$api_endpoint" -H "'$headers'" -d "'$body'" -s -o /dev/null -w "%{http_code}" )"

    if [[ "$test_result" == "200" ]]; then
        echo "API $api_endpoint test passed"
    else
        echo "API $api_endpoint test failed ($status)"

        echo curl --write-out "%{http_code}" --silent --output -X "$invoke_method" "$api_endpoint" -H "'$headers'" -d "'$body'"

        echo "API OUTPUT:"
        echo "$test_result"

        echo "LAMBDA OUTPUT:"
        cat $log_temp_file |jq .LogResult | sed 's/^"//' | sed 's/"$//' | base64 --decode

        return 1
    fi
}