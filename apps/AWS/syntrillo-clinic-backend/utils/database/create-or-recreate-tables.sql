USE syntrillo$PseudonymManagement;

-- DROP TABLE IF EXISTS logs;
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,                      # Auto-increment ID for unique identification
    date DATETIME DEFAULT CURRENT_TIMESTAMP,                # Date and time of the log entry
    event VARCHAR(255) NOT NULL,                            # Brief description of the event
    json_data JSON,                                         # Additional data associated with the event in JSON format
    comment TEXT                                            # Additional comments about the log entry
);

-- DROP TABLE IF EXISTS user_look_up_codes;
CREATE TABLE IF NOT EXISTS user_look_up_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,                      # Auto-increment ID for unique identification

    # Internal key, fixed length for consistency
    #  DEFAULT (UUID_TO_BIN(UUID())) generated a UUID version 1 : not suitable for this use case. Using python uuid4() instead
    syntrillo_internal_key BINARY(16) UNIQUE ,

    # Pseudonymized code for access control
    #  DEFAULT (UUID_TO_BIN(UUID())) generated a UUID version 1 : not suitable for this use case. Using python uuid4() instead
    pseudo_code_for_tenovi_phi_access BINARY(16) UNIQUE ,

    # External user ID, fixed length for consistency
    healthie_user_id CHAR(255) UNIQUE,

    # Date of creation for audit purposes
    date DATETIME DEFAULT CURRENT_TIMESTAMP,  # Defaulting to now

    # Enforce unique relationships
    UNIQUE(syntrillo_internal_key, healthie_user_id),
    UNIQUE(syntrillo_internal_key, pseudo_code_for_tenovi_phi_access)
);

-- DROP TABLE IF EXISTS user_look_up_temporary_codes;
CREATE TABLE IF NOT EXISTS user_look_up_temporary_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,                  # Auto-increment ID for unique identification

    # Internal key, fixed length for consistency, UUID version 4 from user_look_up_codes
    # not unique here, as it can have multiple temporary codes
    syntrillo_internal_key BINARY(16),

    # Temporary pseudonymized code for temporary access (many-to-one relationship with syntrillo_internal_key)
    # This code is used for temporary identification and is scheduled for deletion
    # Could be a basic TwoWords code for Tenovi, or a UUID for iFrame => CHAR(255) for flexibility
    temporary_pseudo_code CHAR(255) UNIQUE,

    # Purpose of this code. For example 'iFrame', 'Tenovi'
    purpose CHAR(255),

    # Date of creation for scheduled deletion
    date DATETIME DEFAULT CURRENT_TIMESTAMP,  # Defaulting to now

    INDEX (syntrillo_internal_key),
    INDEX (temporary_pseudo_code)
);

# ---

USE syntrillo$HealthInformation;

-- DROP TABLE IF EXISTS tenovi_raw_measurements;
CREATE TABLE IF NOT EXISTS tenovi_raw_measurements (
    id                          INT AUTO_INCREMENT PRIMARY KEY,
    syntrillo_internal_key      BINARY(16) NOT NULL,
    device_name                 VARCHAR(255) NOT NULL,
    metric_name                 VARCHAR(255) NOT NULL,      -- json data copied here to speed-up access
    value_1                     VARCHAR(255) DEFAULT NULL,
    value_2                     VARCHAR(255) DEFAULT NULL,
    timestamp_local             VARCHAR(255) NOT NULL,  -- this is timestamp isoformat: patient local time + timezone_offset from the device
    data_json                   JSON NOT NULL,
    date                        DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX (syntrillo_internal_key),
    INDEX (device_name)
);

-- DROP TABLE IF EXISTS healthie_form_templates;
CREATE TABLE IF NOT EXISTS healthie_form_templates (
    form_id VARCHAR(255) NOT NULL,
    module_id VARCHAR(255) NOT NULL,
    form_name VARCHAR(255) DEFAULT NULL,
    module_label TEXT DEFAULT NULL,
    module_options TEXT DEFAULT NULL,
    PRIMARY KEY (form_id, module_id)
);

-- DROP TABLE IF EXISTS healthie_form_responses;
CREATE TABLE IF NOT EXISTS healthie_form_responses (
    module_id VARCHAR(255) NOT NULL,
    form_id VARCHAR(255) NOT NULL,
    syntrillo_internal_key VARCHAR(255) NOT NULL,
    answer TEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (module_id, form_id, syntrillo_internal_key)
);

-- DROP TABLE IF EXISTS module_label_look_up;
CREATE TABLE IF NOT EXISTS module_label_look_up (
  module_label VARCHAR(255) NOT NULL,
  form_id_prod VARCHAR(255) NOT NULL,
  module_id_prod VARCHAR(255) NOT NULL,
  form_id_staging VARCHAR(255) NOT NULL,
  module_id_staging VARCHAR(255) NOT NULL
);

-- DROP TABLE IF EXISTS patient_medications;
CREATE TABLE IF NOT EXISTS patient_medications (
    syntrillo_internal_key VARCHAR(255) NOT NULL,
    med_name VARCHAR(255) NOT NULL,
    med_dosage VARCHAR(255),
    directions VARCHAR(255),
    compliance VARCHAR(255),
    PRIMARY KEY (syntrillo_internal_key, med_name)
);

CREATE TABLE IF NOT EXISTS billing_records (
    service_line_id VARCHAR(255) NOT NULL,
    claim_id VARCHAR(255) NOT NULL,
    encounter_id VARCHAR(255) NOT NULL,
    claim_status VARCHAR(255) NOT NULL,
    syntrillo_internal_key VARCHAR(255) NOT NULL,
    cpt_code VARCHAR(255),
    date_of_service_start VARCHAR(255) NOT NULL,
    date_of_service_end VARCHAR(255),
    PRIMARY KEY (service_line_id)
);

CREATE TABLE IF NOT EXISTS billing_eligibility (
    syntrillo_internal_key VARCHAR(255) NOT NULL,
    cpt_code VARCHAR(15),
    bp_device_training_status BOOLEAN DEFAULT FALSE,
    eligible_to_bill BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (syntrillo_internal_key)
)
