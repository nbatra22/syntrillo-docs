DROP USER 'syntrillo_clinic_readonly_dev';
CREATE USER 'syntrillo_clinic_readonly_dev' IDENTIFIED BY 'xxx';
FLUSH PRIVILEGES; # <== Important or you get an access denied error

GRANT SELECT ON syntrillo$HealthInformation.* TO 'syntrillo_clinic_readonly_dev'@'%';
FLUSH PRIVILEGES;
GRANT SELECT ON syntrillo$PseudonymManagement.* TO 'syntrillo_clinic_readonly_dev'@'%';
FLUSH PRIVILEGES;
GRANT SELECT ON syntrillo$ChatbotsInformation.* TO 'syntrillo_clinic_readonly_dev'@'%';
FLUSH PRIVILEGES;