# # # TEST IFRAMES

# # RESOURCE_PATH='/healthie/iframe_provider_tab/system_devices/tenovi_pair_devices_form'

# # echo
# # echo "Remote Iframe Test ($RESOURCE_PATH)"

# # PAYLOAD='{"httpMethod": "POST", "path": "'$RESOURCE_PATH'", "queryStringParameters": "", "body": "temporary_lookup_code=750335a3-d8bb-49cb-9e57-559f6441e099"}'

# # TEST=$(aws lambda invoke \
# #     --cli-binary-format raw-in-base64-out \
# #     --function-name IFrameGeneratorFunction \
# #     --cli-binary-format raw-in-base64-out \
# #     --payload "$PAYLOAD" \
# #     --log-type Tail \
# #     --query 'LogResult' \
# #     --output text \
# #     /tmp/test.json > /tmp/test-with-logs.json)

# # ERROR_MESSAGE=$(cat /tmp/test.json | jq .errorMessage)

# # if [ "$ERROR_MESSAGE" == "null" ]; then
# #     echo "IFrame Generator function ($RESOURCE_PATH) test passed"
# # else
# #     echo "IFrame Generator function ($RESOURCE_PATH) test failed"
# #     cat /tmp/test.json | jq # in the case of "/" $RESOURCE_PATH, file is /tmp/.json
# #     exit 1
# # fi

# # STATUS_CODE=$(cat /tmp/test.json | jq .statusCode)
# # if [ "$STATUS_CODE" == "\"200\"" ]; then
# #     echo "IFrame Generator function ($RESOURCE_PATH) test passed"
# # else
# #     echo "IFrame Generator function test failed"
# #     cat /tmp/test.json | jq
# #     cat /tmp/test-with-logs.json | base64 --decode
# #     exit 1
# # fi



# CHECK FOUNDATIONS IFRAMES

RESOURCE_PATHES="\
/check_internet_ingress \
/check_internet_egress \
/check_mysql_database_access \
"

for resource_path in $RESOURCE_PATHES; do
    RESOURCE_PATH=$resource_path
    
    echo
    echo "Remote Function Test ($RESOURCE_PATH)"

    TEST=$(aws lambda invoke \
        --cli-binary-format raw-in-base64-out \
        --function-name CheckConnectivityFunction \
        --cli-binary-format raw-in-base64-out \
        --payload "{ \"path\": \"$RESOURCE_PATH\" }" \
        /tmp/$RESOURCE_PATH.json)

    ERROR_MESSAGE=$(cat /tmp/$RESOURCE_PATH.json | jq .errorMessage)

    if [ "$ERROR_MESSAGE" == "null" ]; then
        echo "ConnectivityCheckFunction ($RESOURCE_PATH) test passed"
    else
        echo "ConnectivityCheckFunction ($RESOURCE_PATH) test failed"
        cat /tmp/$RESOURCE_PATH.json | jq
        exit 1
    fi

    STATUS_CODE=$(cat /tmp/$RESOURCE_PATH.json | jq .statusCode)
    if [ "$STATUS_CODE" == "200" ]; then
        echo "ConnectivityCheckFunction ($RESOURCE_PATH) test passed"
    else
        echo "ConnectivityCheckFunction test failed"
        cat /tmp/$RESOURCE_PATH.json | jq
        exit 1
    fi

    echo
    echo "Remote Api Test ($RESOURCE_PATH)"

    REST_API_ID=$(aws apigateway get-rest-apis --query "items[?name=='CheckConnectivityAPI'].id" --output text)
    RESOURCE_ID=$(aws apigateway get-resources --rest-api-id $REST_API_ID --query "items[?path=='$RESOURCE_PATH'].id" --output text)
    TEST=$(aws apigateway test-invoke-method \
        --rest-api-id $REST_API_ID \
        --resource-id $RESOURCE_ID \
        --http-method GET \
        --path-with-query-string $RESOURCE_PATH \
        --body '')

    STATUS=$(echo $TEST | jq .status)

    if [ "$STATUS" == "200" ]; then
        echo "CheckConnectivityAPI ($RESOURCE_PATH) test passed"
    else
        echo "CheckConnectivityAPI ($RESOURCE_PATH) test failed"
        echo $TEST | jq .
        echo "### LAMBDA FUNCTION RESPONSE (CAN HELP TO UNDERSTAND THE ISSSUE SOMETIMES)"
        cat /tmp/$RESOURCE_PATH.json | jq .
        exit 1
    fi
done

RESOURCE_PATHES="\
/check_python_module_import \
"

for resource_path in $RESOURCE_PATHES; do
    RESOURCE_PATH=$resource_path
    
    echo
    echo "Remote Function Test ($RESOURCE_PATH)"

    TEST=$(aws lambda invoke \
        --cli-binary-format raw-in-base64-out \
        --function-name CheckBehaviourFunction \
        --cli-binary-format raw-in-base64-out \
        --payload "{ \"path\": \"$RESOURCE_PATH\" }" \
        /tmp/$RESOURCE_PATH.json)

    ERROR_MESSAGE=$(cat /tmp/$RESOURCE_PATH.json | jq .errorMessage)

    if [ "$ERROR_MESSAGE" == "null" ]; then
        echo "CheckBehaviourFunction ($RESOURCE_PATH) test passed"
    else
        echo "CheckBehaviourFunction ($RESOURCE_PATH) test failed"
        cat /tmp/$RESOURCE_PATH.json | jq
        exit 1
    fi

    STATUS_CODE=$(cat /tmp/$RESOURCE_PATH.json | jq .statusCode)
    if [ "$STATUS_CODE" == "200" ]; then
        echo "CheckBehaviourFunction ($RESOURCE_PATH) test passed"
    else
        echo "CheckBehaviourFunction test failed"
        cat /tmp/$RESOURCE_PATH.json | jq
        exit 1
    fi

    echo
    echo "Remote Api Test ($RESOURCE_PATH)"

    REST_API_ID=$(aws apigateway get-rest-apis --query "items[?name=='CheckBehaviourAPI'].id" --output text)
    RESOURCE_ID=$(aws apigateway get-resources --rest-api-id $REST_API_ID --query "items[?path=='$RESOURCE_PATH'].id" --output text)
    TEST=$(aws apigateway test-invoke-method \
        --rest-api-id $REST_API_ID \
        --resource-id $RESOURCE_ID \
        --http-method GET \
        --path-with-query-string $RESOURCE_PATH \
        --body '')

    STATUS=$(echo $TEST | jq .status)

    if [ "$STATUS" == "200" ]; then
        echo "CheckConnectivityAPI ($RESOURCE_PATH) test passed"
    else
        echo "CheckConnectivityAPI ($RESOURCE_PATH) test failed"
        echo $TEST | jq .
        echo "### LAMBDA FUNCTION RESPONSE (CAN HELP TO UNDERSTAND THE ISSSUE SOMETIMES)"
        cat /tmp/$RESOURCE_PATH.json | jq .
        exit 1
    fi
done

# TEST IFRAMES (GET)

RESOURCE_PATHES="\
/ \
/iframe_healthie_provider_tab \
"

FUNCTION_NAME="IFrameGeneratorFunction"

for resource_path in $RESOURCE_PATHES; do
    RESOURCE_PATH=$resource_path
    PATH_BASE_NAME=$(basename $RESOURCE_PATH)

    echo
    echo "Remote Iframe Test ($RESOURCE_PATH)"

    PAYLOAD='{"httpMethod": "GET", "path": "'$resource_path'", "queryStringParameters": ""}'

    TEST=$(aws lambda invoke \
        --cli-binary-format raw-in-base64-out \
        --function-name $FUNCTION_NAME \
        --cli-binary-format raw-in-base64-out \
        --payload "$PAYLOAD" \
        /tmp/$PATH_BASE_NAME.json)

    ERROR_MESSAGE=$(cat /tmp/$PATH_BASE_NAME.json | jq .errorMessage)

    if [ "$ERROR_MESSAGE" == "null" ]; then
        echo "IFrame Generator function ($RESOURCE_PATH) test passed"
    else
        echo "IFrame Generator function ($RESOURCE_PATH) test failed"
        cat /tmp/$PATH_BASE_NAME.json | jq # in the case of "/" $RESOURCE_PATH, file is /tmp/.json
        exit 1
    fi

    STATUS_CODE=$(cat /tmp/$PATH_BASE_NAME.json | jq .statusCode)
    if [ "$STATUS_CODE" == "\"200\"" ]; then
        echo "IFrame Generator function ($RESOURCE_PATH) test passed"
    else
        echo "IFrame Generator function test failed"
        cat /tmp/$PATH_BASE_NAME.json | jq
        exit 1
    fi

    echo
    echo "Remote Api Test ($RESOURCE_PATH)"

    REST_API_ID=$(aws apigateway get-rest-apis --query "items[?name=='IFramGeneratorAPI'].id" --output text)
    RESOURCE_ID=$(aws apigateway get-resources --rest-api-id $REST_API_ID --query "items[?path=='$RESOURCE_PATH'].id" --output text)
    TEST=$(aws apigateway test-invoke-method \
        --rest-api-id $REST_API_ID \
        --resource-id $RESOURCE_ID \
        --http-method GET \
        --path-with-query-string $RESOURCE_PATH \
        --body '')

    STATUS=$(echo $TEST | jq .status)

    if [ "$STATUS" == "200" ]; then
        echo "IFrame Generator API ($RESOURCE_PATH) test passed"
    else
        echo "IFrame Generator API ($RESOURCE_PATH) test failed"
        echo $TEST | jq .
        echo "### LAMBDA FUNCTION RESPONSE (CAN HELP TO UNDERSTAND THE ISSSUE SOMETIMES)"
        cat /tmp/$PATH_BASE_NAME.json | jq .
        exit 1
    fi

done

# TEST IFRAMES (POST)

event='''{
"temporary_lookup_code": "84bbd0cd-d8d5-40cc-b993-d50f8d98ba66",
"date_start_ago": "one-week-ago",
"date_end_ago": "today",
"blood_pressure_state": "healthy",
"heart_rate_state": "healthy",
"steps_state": "healthy",
"medication_adherence_state": "perfect",
"medication_expected_pattern": "twice_daily"
}'''

RESOURCE_PATHES="\
/healthie/iframe_provider_tab/devices/tenovi_order_new_devices_form \
/healthie/iframe_provider_tab/system_devices/tenovi_dummy_data_generator_form \
"

FUNCTION_NAME="IFrameGeneratorFunction"

for resource_path in $RESOURCE_PATHES; do
    RESOURCE_PATH=$resource_path
    PATH_BASE_NAME=$(basename $RESOURCE_PATH)

    echo
    echo "Remote Iframe Test ($RESOURCE_PATH)"

    echo "$PAYLOAD" > /tmp/payload.json

    echo $PAYLOAD

    TEST=$(aws lambda invoke \
        --cli-binary-format raw-in-base64-out \
        --function-name $FUNCTION_NAME \
        --cli-binary-format raw-in-base64-out \
        --payload "fileb://event-samples/$PATH_BASE_NAME.json" \
        --log-type Tail \
        --query 'LogResult' \
        --output text \
        /tmp/$PATH_BASE_NAME.json > /tmp/$PATH_BASE_NAME.logs)

    ERROR_MESSAGE=$(cat /tmp/$PATH_BASE_NAME.json | jq .errorMessage)

    if [ "$ERROR_MESSAGE" == "null" ]; then
        echo "IFrame Generator function ($RESOURCE_PATH) test passed"
    else
        echo "IFrame Generator function ($RESOURCE_PATH) test failed"
        cat /tmp/$PATH_BASE_NAME.json | jq # in the case of "/" $RESOURCE_PATH, file is /tmp/.json
        exit 1
    fi

    STATUS_CODE=$(cat /tmp/$PATH_BASE_NAME.json | jq .statusCode)
    echo $STATUS_CODE
    if [ "$STATUS_CODE" == "\"200\"" ]; then
        echo "IFrame Generator function ($RESOURCE_PATH) test passed"
    else
        echo "IFrame Generator function ($RESOURCE_PATH) test failed"
        cat /tmp/$PATH_BASE_NAME.json | jq
        cat /tmp/$PATH_BASE_NAME.logs | base64 --decode
        exit 1
    fi

    echo
    echo "Remote Api Test ($RESOURCE_PATH)"

    REST_API_ID=$(aws apigateway get-rest-apis --query "items[?name=='IFramGeneratorAPI'].id" --output text)
    RESOURCE_ID=$(aws apigateway get-resources --rest-api-id $REST_API_ID --query "items[?path=='$RESOURCE_PATH'].id" --output text)
    TEST=$(aws apigateway test-invoke-method \
        --rest-api-id $REST_API_ID \
        --resource-id $RESOURCE_ID \
        --http-method POST \
        --path-with-query-string $RESOURCE_PATH \
        --body 'temporary_lookup_code=520ca46e-99a5-4bc2-9f32-c0e4c283969c&gateway_id=None&device_bpm_large=yes&device_pillbox=yes&device_watch=yes')

    STATUS=$(echo $TEST | jq .status)

    if [ "$STATUS" == "200" ]; then
        echo "IFrame Generator API ($RESOURCE_PATH) test passed"
    else
        echo "IFrame Generator API ($RESOURCE_PATH) test failed"
        echo $TEST | jq .
        echo "### LAMBDA FUNCTION RESPONSE (CAN HELP TO UNDERSTAND THE ISSSUE SOMETIMES)"
        cat /tmp/$PATH_BASE_NAME.json | jq .
        exit 1
    fi

done


cd ../..
python3 tests/apis/test-apis-foundation.py
cd -

cd ../..
python3 tests/apis/test-apis-iframes.py
cd -

