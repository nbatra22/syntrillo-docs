#!/bin/bash

ENVIRONMENT="sandbox"

if [ "$(which session-manager-plugin)" == "" ]; then
  echo "!!!Please install session-manager-plugin"
  echo "Documentation link: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
  echo "Example on ubuntu or debian:"
  echo '$> curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb'
  echo "$> sudo dpkg -i session-manager-plugin.deb"
  exit
fi

PROFILE="syntrillo-genai-$ENVIRONMENT"

INSTANCE_ID=$(aws ec2 describe-instances --profile $PROFILE \
    --filters "Name=tag:Name,Values=SyntrilloGenAiBackendSandboxInstance" "Name=instance-state-name,Values=running" \
    --query "Reservations[*].Instances[*].InstanceId" \
    --output text)


aws ssm --profile $PROFILE \
    start-session \
    --target $INSTANCE_ID \
    --document-name AWS-StartInteractiveCommand --parameters command="sudo su - ubuntu"



