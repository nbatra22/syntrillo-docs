USE syntrillo$HealthInformation;

DROP TABLE IF EXISTS healthie_questionnaires;

CREATE TABLE IF NOT EXISTS healthie_questionnaires (
    id                          INT AUTO_INCREMENT PRIMARY KEY,
    platform                    VARCHAR(255) DEFAULT NULL,
    name                        VARCHAR(255) NOT NULL,
    version                     VARCHAR(255) NOT NULL,
    structure_json              JSON NOT NULL,
    excel_file                  MEDIUMBLOB DEFAULT NULL,
    date                        DATETIME DEFAULT CURRENT_TIMESTAMP
);
