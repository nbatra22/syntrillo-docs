
for resource_path in "/check_internet_ingress" "/check_internet_egress" "/check_python_module_import"; do
    RESOURCE_PATH=$resource_path
    
    echo
    echo "Remote Api Test ($RESOURCE_PATH)"

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
        cat /tmp/$RESOURCE_PATH.json | jq .
        exit 1
    fi
done

cd ../..
python3 tests/apis/test-apis-foundation.py