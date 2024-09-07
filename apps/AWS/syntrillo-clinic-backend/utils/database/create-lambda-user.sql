DROP USER 'syntrillo_clinic_lambda_user';
CREATE USER 'syntrillo_clinic_lambda_user' IDENTIFIED BY "xxx";
GRANT SELECT, INSERT, UPDATE ON syntrillo$HealthInformation.* TO 'syntrillo_clinic_lambda_user'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON syntrillo$PseudonymManagement.* TO 'syntrillo_clinic_lambda_user'@'%';
GRANT LOCK TABLES ON syntrillo$PseudonymManagement.* TO 'syntrillo_clinic_lambda_user'@'%';
FLUSH PRIVILEGES; # <== Important or you get an access denied error