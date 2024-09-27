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

hostname="127.0.0.1"
local_port=5000

echo "-----"
echo "$> curl --location 'http://$hostname:$local_port/query' ... #W IN ANOTHER TERMINAL"
echo "-----"

aws ssm --profile $PROFILE \
    start-session \
    --target $INSTANCE_ID \
    --document-name AWS-StartPortForwardingSessionToRemoteHost \
    --parameters '{"host":["'$hostname'"],"portNumber":["5000"], "localPortNumber":["'$local_port'"]}' &

# Allow the session to establish
sleep 10

# Keep-alive loop: Ping the local port periodically to keep the session active
while true; do
    echo -ne "\nPinging localhost:$local_port to keep tunnel alive..."
    (echo > /dev/tcp/localhost/$local_port) >/dev/null 2>&1 || echo -e "\nPing failed"
    sleep 300  # Ping every 5 minutes
done
