ENVIRONMENT=$1
if [ "$ENVIRONMENT" == 'sandbox' ]; then
  SECRET_NAME='SyntrilloClinicBackendStack-oSWB6kcdQXhb'
fi

if [ "$ENVIRONMENT" == 'staging' ]; then
  SECRET_NAME='SyntrilloClinicBackendStack-vdxv5amcc1Vs'
fi

password=$(aws secretsmanager --profile syntrillo-clinic-$ENVIRONMENT \
		get-secret-value \
		--secret-id $SECRET_NAME \
		--query 'SecretString' \
		--output text | jq -r '.password')

echo '---'
echo "MYSQL DATABASE $ENVIRONMENT PASSWORD: $password"
echo "!!! N.B. : Using password is temporary, we should connect with IAM roles in the future"
echo '---'

#password=$(aws secretsmanager --profile syntrillo-clinic-sandbox get-secret-value --secret-id SyntrilloClinicBackendStack-oSWB6kcdQXhb --query 'SecretString' --output text | jq -r '.password')
mysql -h 127.0.0.1 -P 3307 -u admin -p$password
if [ $? != 0 ]; then
  echo "!!!"
  echo "Make sure you have opened the sql-tunnel"
  echo "!!!"
fi
