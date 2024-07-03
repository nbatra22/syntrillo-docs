
for resource_path in "/test_internet_egress"; do
    RESOURCE_PATH=$resource_path
    
    echo "CALL ConnectivityCheckFunction ($RESOURCE_PATH) (Remote)"

    TEST=$(aws lambda invoke \
        --cli-binary-format raw-in-base64-out \
        --function-name CheckConnectivityFunction \
        --cli-binary-format raw-in-base64-out \
        --payload "{ \"path\": \"$RESOURCE_PATH\" }" \
        /tmp/$RESOURCE_PATH.json)

    ERROR_MESSAGE=$(cat /tmp/$RESOURCE_PATH.json | jq .errorMessage)

    if [ "$ERROR_MESSAGE" == "null" ]; then
        echo "ConnectivityCheckAPI test passed"
    else
        echo "ConnectivityCheckAPI test failed"
        cat /tmp/$RESOURCE_PATH.json | jq
        exit 1
    fi

    echo "CALL ConnectivityCheckAPI ($RESOURCE_PATH) (Remote)"
    REST_API_ID=$(aws apigateway get-rest-apis --query "items[?name=='CheckConnectivityAPI'].id" --output text)
    RESOURCE_ID=$(aws apigateway get-resources --rest-api-id 8h80w03imj --query "items[?path=='$RESOURCE_PATH'].id" --output text)
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