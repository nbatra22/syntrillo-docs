# Set here the name of the stack you want to deploy
STACK_NAME=BloodPressureNotifierStack

# AWS profile to use for deployment
# check ~/.aws/config for the profile name
PROFILE=syntrillo-clinic-staging-deployment

# One-time command to prepare the AWS environment (account/region) for CDK deployments
bootstrap:
	cdk bootstrap --profile $(PROFILE)

# Compare the local stack with the staging stack
diff-with-remote:
	./utils/cdk-diff-with-staging.sh $(STACK_NAME)

# Deploy the stack to staging
deploy:
	./utils/cdk-deploy-to-staging.sh $(STACK_NAME)
