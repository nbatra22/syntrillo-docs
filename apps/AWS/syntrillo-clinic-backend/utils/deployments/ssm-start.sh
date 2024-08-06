ENVIRONMENT=$1
SESSION_TYPE=$2

# FOR SSH CONNECTION: INSTALL session-manager-plugin
# https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

PROFILE="syntrillo-clinic-$ENVIRONMENT"

# Find instance id with name as BastionHost
INSTANCE_ID=$(aws ec2 describe-instances --profile $PROFILE \
    --filters "Name=tag:Name,Values=BastionHost" \
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
    echo "-----"
    echo "$> mysql -h 127.0.0.1 -P 3307 -u admin -p # => To excute in another terminal"
    echo "-----"
    if [ $ENVIRONMENT == 'sandbox' ]; then
        hostname="syntrilloclinicbackendstackd-mysqldatabase22bdac80-5kt0pwavmcmm.cf60aoaem0ky.us-east-1.rds.amazonaws.com"        
    fi
    if [ $ENVIRONMENT == 'staging' ]; then
        hostname="syntrilloclinicbackendstackd-mysqldatabase22bdac80-k1mp4rbufthl.cv68uwgwk82p.us-east-1.rds.amazonaws.com"
    fi
    
    aws ssm --profile $PROFILE \
        start-session \
    --target $INSTANCE_ID \
        --document-name AWS-StartPortForwardingSessionToRemoteHost \
        --parameters '{"host":["syntrilloclinicbackendstackd-mysqldatabase22bdac80-k1mp4rbufthl.cv68uwgwk82p.us-east-1.rds.amazonaws.com"],"portNumber":["3306"], "localPortNumber":["3307"]}'
    # ---
    # THEN: 
fi