if [ "$(which jq)" == "" ]; then
  echo "!!!Please install jq"
  echo "example on ubuntu: sudo apt-get install jq"
  exit
fi

SECRET_NAME='...'

host=$(aws secretsmanager \
                get-secret-value \
                --secret-id $SECRET_NAME \
                --query 'SecretString' \
                --output text | jq -r '.host')

username=$(aws secretsmanager \
                get-secret-value \
                --secret-id $SECRET_NAME \
                --query 'SecretString' \
                --output text | jq -r '.username')

password=$(aws secretsmanager \
                get-secret-value \
                --secret-id $SECRET_NAME \
                --query 'SecretString' \
                --output text | jq -r '.password')

local_port='3306'

echo '---'
echo "ENVIRONEMENT: $ENVIRONMENT"
echo "MYSQL DATABASE $ENVIRONMENT USER NAME: $username"
echo "MYSQL DATABASE $ENVIRONMENT PASSWORD: $password"
echo '---'

echo "---"
mysql -h $host -P $local_port -u $username -p$password --ssl