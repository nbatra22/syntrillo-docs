import boto3
import json
import base64
import os

def invoke_api_resource(resource_path, api_name, invoke_method, headers, body):
    # Initialize boto3 client
    apigateway = boto3.client('apigateway')

    resource_id_path = resource_path

    # Handle proxy+ path
    base_path = '/'.join(resource_path.split('/')[:-1])
    if base_path:
        resource_id_path = f"{base_path}/{{proxy+}}"

    # Get REST API ID
    rest_apis = apigateway.get_rest_apis()
    rest_api_id = next((api['id'] for api in rest_apis['items'] if api['name'] == api_name), None)

    if not rest_api_id:
        raise ValueError(f"API with name {api_name} not found")

    # Get resource ID
    resources = apigateway.get_resources(restApiId=rest_api_id)
    resource_id = next((resource['id'] for resource in resources['items'] if resource['path'] == resource_id_path), None)

    if not resource_id:
        raise ValueError(f"Resource with path {resource_id_path} not found")

    # Test invoke method
    test_result = apigateway.test_invoke_method(
        restApiId=rest_api_id,
        resourceId=resource_id,
        httpMethod=invoke_method,
        pathWithQueryString=resource_path,
        headers=headers,
        body=body
    )

    status = test_result['status']

    if status == 200:
        print(f"API {api_name} ({resource_path}) test passed")
    else:
        print(f"API {api_name} ({resource_path}) test failed ({status})")
        
        print("INVOKE:")
        print(f"aws apigateway get-rest-apis --query \"items[?name=='{api_name}'].id\" --output text")
        print(f"aws apigateway get-resources --rest-api-id \"{rest_api_id}\" --query \"items[?path=='{resource_path}'].id\" --output text")
        print(f"aws apigateway test-invoke-method --rest-api-id \"{rest_api_id}\" --resource-id \"{resource_id}\" "
              f"--http-method {invoke_method} --path-with-query-string \"{resource_path}\" "
              f"--headers \"{json.dumps(headers)}\" --body \"{body}\"")

        print("API OUTPUT:")
        print(json.dumps(test_result, indent=2))

        print("LAMBDA OUTPUT:")
        if 'log' in test_result:
            log_result = test_result['log']
            try:
                decoded_log = base64.b64decode(log_result).decode('utf-8')
                print(decoded_log)
            except:
                print("Failed to decode log output")

        return False

    return True

# Example usage
if __name__ == "__main__":
    resource_path = "/ping"
    api_name = "IFramGeneratorAPI"
    invoke_method = "GET"
    headers = {"Content-Type": "application/json"}
    body = "{}"

    invoke_api_resource(resource_path, api_name, invoke_method, headers, body)