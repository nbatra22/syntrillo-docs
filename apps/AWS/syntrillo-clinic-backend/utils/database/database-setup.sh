# install mariadb/mysql client
sudo yum install mariadb105

# Create a user that can authenticate with IAM Role
CREATE USER 'syntrillo_clinic_lambda_user' IDENTIFIED WITH AWSAuthenticationPlugin as 'RDS';
FLUSH PRIVILEGES; # <== Important or you get an access denied error
GRANT SELECT, INSERT, UPDATE, DELETE ON syntrillo$HealthInformation.* TO 'syntrillo_clinic_lambda_user'@'%';
FLUSH PRIVILEGES;
GRANT SELECT, INSERT, UPDATE, DELETE ON syntrillo$PseudonymManagement.* TO 'syntrillo_clinic_lambda_user'@'%';
FLUSH PRIVILEGES;