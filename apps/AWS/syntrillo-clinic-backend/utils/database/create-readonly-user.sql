DROP USER 'syntrillo_clinic_readonly_user';
CREATE USER 'syntrillo_clinic_readonly_user' IDENTIFIED WITH AWSAuthenticationPlugin as 'RDS';
FLUSH PRIVILEGES; # <== Important or you get an access denied error
GRANT SELECT ON syntrillo$HealthInformation.* TO 'syntrillo_clinic_readonly_user'@'%';
FLUSH PRIVILEGES;
GRANT SELECT ON syntrillo$PseudonymManagement.* TO 'syntrillo_clinic_readonly_user'@'%';
FLUSH PRIVILEGES;