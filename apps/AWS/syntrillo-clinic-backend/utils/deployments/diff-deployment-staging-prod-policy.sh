#!/bin/bash

profile="syntrillo-clinic-staging"
latest_version=$(aws iam --profile $profile list-policies --query 'Policies[?PolicyName==`SyntrilloClinicBackendCdkCloudFormationExecutionPolicyProdlike`].DefaultVersionId' --output text)
aws iam --profile $profile get-policy-version --policy-arn arn:aws:iam::021891579520:policy/SyntrilloClinicBackendCdkCloudFormationExecutionPolicyProdlike  --version-id "$latest_version" \
|jq 'del(.PolicyVersion.VersionId, .PolicyVersion.CreateDate)' > staging-policy.json
sed -i 's/021891579520/381491864638/g' staging-policy.json

profile="syntrillo-clinic-staging"
latest_version=$(aws iam --profile $profile list-policies --query 'Policies[?PolicyName==`SyntrilloClinicBackendTasksCdkCloudFormationExecutionPolicyProdlike`].DefaultVersionId' --output text)
aws iam --profile $profile get-policy-version --policy-arn arn:aws:iam::021891579520:policy/SyntrilloClinicBackendTasksCdkCloudFormationExecutionPolicyProdLike --version-id "$latest_version" \
|jq 'del(.PolicyVersion.VersionId, .PolicyVersion.CreateDate)' > tasks-staging-policy.json
sed -i 's/021891579520/381491864638/g' tasks-staging-policy.json

profile="syntrillo-clinic-prod-deployment"
latest_version=$(aws iam --profile $profile list-policies --query 'Policies[?PolicyName==`SyntrilloClinicBackendCdkCloudFormationExecutionPolicy`].DefaultVersionId' --output text)
aws iam --profile $profile get-policy-version --policy-arn arn:aws:iam::381491864638:policy/SyntrilloClinicBackendCdkCloudFormationExecutionPolicy  --version-id "$latest_version" \
|jq 'del(.PolicyVersion.VersionId, .PolicyVersion.CreateDate)' > prod-policy.json

profile="syntrillo-clinic-prod-deployment"
latest_version=$(aws iam --profile $profile list-policies --query 'Policies[?PolicyName==`SyntrilloClinicBackendTasksCdkCloudFormationExecutionPolicy`].DefaultVersionId' --output text)
aws iam --profile $profile get-policy-version --policy-arn arn:aws:iam::381491864638:policy/SyntrilloClinicBackendTasksCdkCloudFormationExecutionPolicy --version-id "$latest_version" \
|jq 'del(.PolicyVersion.VersionId, .PolicyVersion.CreateDate)' > tasks-prod-policy.json

echo "[ DIFF BackendPolicy]"
diff prod-policy.json staging-policy.json
echo "[ DIFF TasksBackendPolicy]"
diff tasks-prod-policy.json tasks-staging-policy.json

rm staging-policy.json prod-policy.json tasks-staging-policy.json tasks-prod-policy.json
