#!/bin/bash -e

source ~/SyntrilloClinic/apps/AWS/syntrillo-clinic-backend/tests/remote/_invoke-lambdas-and-api-functions.sh

# Connectivity checks
CONNECTIVITY_CHECK_PATHS=("/check_internet_ingress" "/check_internet_egress" "/check_mysql_database_access")
for resource_path in "${CONNECTIVITY_CHECK_PATHS[@]}"; do
    echo "---"$resource_path
    invoke_lambda_function "CheckConnectivityFunction" "$resource_path" "{\"path\": \"$resource_path\"}"
    test_api_gateway_endpoint "$resource_path" "CheckConnectivityAPI" "GET"
    echo
done

# Behavior checks
BEHAVIOR_CHECK_PATHS=("/check_python_module_import")
for resource_path in "${BEHAVIOR_CHECK_PATHS[@]}"; do
    echo "---"$resource_path
    invoke_lambda_function "CheckBehaviourFunction" "$resource_path" "{\"path\": \"$resource_path\"}"
    test_api_gateway_endpoint "$resource_path" "CheckBehaviourAPI" "GET"
    echo
done
