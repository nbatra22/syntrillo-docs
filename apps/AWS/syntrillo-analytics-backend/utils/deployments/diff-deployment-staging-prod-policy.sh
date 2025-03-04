#!/bin/bash

profile="syntrillo-clinic-staging"
latest_version=$(aws iam --profile $profile list-policies --query 'Policies[?PolicyName==`SyntrilloAnalyticsBackendCdkCloudFormationExecutionPolicyProdlike`].DefaultVersionId' --output text)
aws iam --profile $profile get-policy-version --policy-arn arn:aws:iam::021891579520:policy/SyntrilloAnalyticsBackendCdkCloudFormationExecutionPolicyProdlike  --version-id "$latest_version" \
|jq 'del(.PolicyVersion.VersionId, .PolicyVersion.CreateDate)' > staging-policy.json
sed -i 's/021891579520/381491864638/g' staging-policy.json

profile="syntrillo-clinic-prod-deployment"
latest_version=$(aws iam --profile $profile list-policies --query 'Policies[?PolicyName==`SyntrilloAnalyticsBackendCdkCloudFormationExecutionPolicy`].DefaultVersionId' --output text)
aws iam --profile $profile get-policy-version --policy-arn arn:aws:iam::381491864638:policy/SyntrilloAnalyticsBackendCdkCloudFormationExecutionPolicy  --version-id "$latest_version" \
|jq 'del(.PolicyVersion.VersionId, .PolicyVersion.CreateDate)' > prod-policy.json


diff prod-policy.json staging-policy.json

rm staging-policy.json prod-policy.json
