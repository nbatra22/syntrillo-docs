echo 'CALL ConnectivityCheckAPI'


REST_API_ID=$(aws apigateway get-rest-apis --query "items[?name=='CheckConnectivityAPI'].id" --output text)
RESOURCE_ID=$(aws apigateway get-resources --rest-api-id 8h80w03imj --query "items[?path=='/'].id" --output text)
TEST=$(aws apigateway test-invoke-method \
    --rest-api-id $REST_API_ID \
    --resource-id $RESOURCE_ID \
    --http-method GET \
    --path-with-query-string / \
    --body '')
    
STATUS=$(echo $TEST | jq .status)

if [ "$STATUS" == "200" ]; then
    echo "ConnectivityCheckAPI test passed"
else
    echo "ConnectivityCheckAPI test failed"
    echo $TEST | jq .
    exit 1
fi

cd ../..
python3 tests/apis/test-apis-foundation.py