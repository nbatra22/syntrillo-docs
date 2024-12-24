#!/bin/bash

if [ "$1" == "" -o "$2" == "" ]; then
  echo "usage: $0 <environment> <session-type>"
  echo "environments: sandbox, staging"
  echo "session-types: session, ssh-tunnel, mysql-tunnel"
  exit
fi

ENVIRONMENT=$1
SESSION_TYPE=$2

if [ "$(which session-manager-plugin)" == "" ]; then
  echo "!!!Please install session-manager-plugin"
  echo "Documentation link: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
  echo "Example on ubuntu or debian:"
  echo '$> curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb'
  echo "$> sudo dpkg -i session-manager-plugin.deb"
  exit
fi

PROFILE="syntrillo-clinic-$ENVIRONMENT"
if [ "$ENVIRONMENT" == "staging" ]; then
  if grep -q "syntrillo-clinic-staging-database" ~/.aws/config; then
    PROFILE="syntrillo-clinic-staging-database"
  fi
fi

# Find instance id with name as BastionHost that is Running
INSTANCE_ID=$(aws ec2 describe-instances --profile $PROFILE \
    --filters "Name=tag:Name,Values=BastionHost" "Name=instance-state-name,Values=running" \
    --query "Reservations[*].Instances[*].InstanceId" \
    --output text)

if [ "$SESSION_TYPE" == "session" ]; then
    aws ssm --profile $PROFILE \
        start-session \
        --target $INSTANCE_ID \
        --document-name AWS-StartInteractiveCommand --parameters command="sudo su - ec2-user"
fi

if [ "$SESSION_TYPE" == "ssh-tunnel" ]; then
    echo "-----"
    echo "!!! The host must have a keypair associated with it in order to connect via SSH"
    echo "$> ssh -i <keypair.pem> -p 9022 ec2-user@localhost # => To excute in another terminal"
    echo "-----"
    aws ssm --profile $PROFILE \
        start-session \
        --target $INSTANCE_ID \
        --document-name AWS-StartPortForwardingSession \
        --parameters '{"portNumber":["22"],"localPortNumber":["9022"]}'
fi

if [ "$SESSION_TYPE" == "mysql-tunnel" ]; then
    if [ $ENVIRONMENT == 'sandbox' ]; then
        hostname="syntrilloclinicbackendsta-mysqldatabasefromsnapsho-pgfocymgbys3.cf60aoaem0ky.us-east-1.rds.amazonaws.com"
    fi
    if [ $ENVIRONMENT == 'staging' ]; then
        hostname="syntrilloclinicbackendsta-mysqldatabasefromsnapsho-saiukm5mugdm.cv68uwgwk82p.us-east-1.rds.amazonaws.com"
    fi

    local_port=3307

    echo "-----"
    echo "Profile: $PROFILE"
    echo "-----"
    echo "$> mysql -h 127.0.0.1 -P $local_port -u admin -p --ssl # => To excute in another terminal"
    echo "OR"
    echo "$> mysql-connect $ENVIRONMENT # => To excute in another terminal, in the utils/database folder"
    echo "-----"

    aws ssm --profile $PROFILE \
        start-session \
        --target $INSTANCE_ID \
        --document-name AWS-StartPortForwardingSessionToRemoteHost \
        --parameters '{"host":["'$hostname'"],"portNumber":["3306"], "localPortNumber":["'$local_port'"]}' &

    # Allow the session to establish
    sleep 10

    # Keep-alive loop: Ping the local port periodically to keep the session active
    while true; do
        echo -ne "\nPinging localhost:$local_port to keep tunnel alive..."
        (echo > /dev/tcp/localhost/$local_port) >/dev/null 2>&1 || echo -e "\nPing failed"
        sleep 300  # Ping every 5 minutes
    done

fi
