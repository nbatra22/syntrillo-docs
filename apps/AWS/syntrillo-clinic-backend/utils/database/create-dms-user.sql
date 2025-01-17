DROP USER 'syntrillo_analytics_dms_user';
CREATE USER 'syntrillo_analytics_dms_user' IDENTIFIED BY "xxx";
GRANT REPLICATION CLIENT ON *.* TO 'syntrillo_analytics_dms_user'@'%'; 
GRANT REPLICATION SLAVE ON *.* TO 'syntrillo_analytics_dms_user'@'%';
GRANT SELECT ON syntrillo$HealthInformation.tenovi_raw_measurements TO 'syntrillo_analytics_dms_user'@'%';
FLUSH PRIVILEGES; # <== Important or you get an access denied error

-- CLient & Slave cannot be appied at the database level, 
-- it's a global privilege (so we should restrict this at the dms task setup level)

SHOW GRANTS FOR 'syntrillo_analytics_dms_user'@'%';
REVOKE ALL PRIVILEGES ON syntrillo$ChatbotsInformation.* FROM 'syntrillo_analytics_dms_user'@'%';