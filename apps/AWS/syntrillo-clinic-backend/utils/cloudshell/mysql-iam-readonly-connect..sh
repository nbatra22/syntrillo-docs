ENVIRONEMENT="staging"

if [ "$(which jq)" == "" ]; then
  echo "!!!Please install jq"
  echo "example on ubuntu: sudo apt-get install jq"
  exit
fi

host='...'

username="syntrillo_clinic_readonly_user"
port='3306'
password=$(aws rds generate-db-auth-token \
                --hostname $host \
                --port $port \
                --region us-east-1 \
                --username $username)


echo '---'
echo "ENVIRONMENT: $ENVIRONMENT"
echo "MYSQL DATABASE $ENVIRONMENT HOST: $host"
echo "MYSQL DATABASE $ENVIRONMENT USER NAME: $username"
echo "MYSQL DATABASE $ENVIRONMENT PASSWORD: $password"
echo '---'


echo "---"
mysql -h $host -P $port -u $username -p$password --ssl