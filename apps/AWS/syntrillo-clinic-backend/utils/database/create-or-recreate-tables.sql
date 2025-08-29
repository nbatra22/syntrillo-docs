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
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (module_id, form_id, syntrillo_internal_key, updated_at)
);

-- DROP TABLE IF EXISTS module_label_look_up;
CREATE TABLE IF NOT EXISTS module_label_look_up (
  module_label VARCHAR(255) NOT NULL,
  form_id VARCHAR(255) NOT NULL,
  module_id VARCHAR(255) NOT NULL
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

CREATE TABLE IF NOT EXISTS srs_form_responses (
    srs_form_response_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    syntrillo_internal_key_patient VARCHAR(255) NOT NULL,
    syntrillo_internal_key_clinician VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Gender VARCHAR(50) NOT NULL,
    HasPreviousStroke BOOLEAN,
    NumberOfStrokes VARCHAR(20),
    LatestStrokeMechanism VARCHAR(50),
    ScreenedForTIA BOOLEAN,
    LikelihoodOfTIA VARCHAR(50),
    TIAMechanism VARCHAR(50),
    HasPriorHeadCT BOOLEAN,
    PriorCTDate TIMESTAMP,
    ChronicInfarctPresent BOOLEAN,
    ChronicInfarctMechanism VARCHAR(50),
    HistoryOfAtrialFibrillation BOOLEAN,
    HistoryOfIronDeficiencyAnemia BOOLEAN,
    HistoryOfArterialClots BOOLEAN,
    HistoryOfVenousClots BOOLEAN,
    HistoryOfCHF BOOLEAN,
    HistoryOfCarotidStenosis BOOLEAN,
    HistoryOfOSA BOOLEAN,
    HistoryOfCAD BOOLEAN,
    HistoryOfValvularHeartDisease BOOLEAN,
    HistoryOfCKD BOOLEAN,
    HistoryOfHyperlipidemia BOOLEAN,
    AnemiaSeverity VARCHAR(20),
    ArterialClotOccurrences VARCHAR(50),
    PFOPresence VARCHAR(50),
    VenousClotOccurrences VARCHAR(20),
    EjectionFraction VARCHAR(50),
    StenosisPercentage VARCHAR(50),
    OSASeverity VARCHAR(50),
    CADType VARCHAR(100),
    Height FLOAT,
    Weight FLOAT,
    AvgSBP FLOAT,
    RHR FLOAT,
    HemoglobinA1c FLOAT,
    PhysicalInactivityLevel VARCHAR(20),
    LDLLevel VARCHAR(50),
    HDLLevel VARCHAR(50),
    TriglyceridesLevel VARCHAR(50),
    Creatinine FLOAT,
    BMI FLOAT,
    PhysicalInactivityHours FLOAT,
    PhysicalActivityMinutes FLOAT,
    Triglycerides FLOAT,
    LDL FLOAT,
    HDL FLOAT,
    CHECK (NumberOfStrokes IN ('One', 'Multiple')),
    CHECK (LatestStrokeMechanism IN ('Small Vessel', 'Large Vessel', 'Cryptogenic', 'Hypercoagulable', 'Structural', 'Cardioembolic')),
    CHECK (LikelihoodOfTIA IN ('High Likelihood', 'TIA not likely')),
    CHECK (TIAMechanism IN ('Small Vessel', 'Large Vessel', 'Cryptogenic', 'Hypercoagulable', 'Structural', 'Cardioembolic')),
    CHECK (ChronicInfarctMechanism IN ('Small Vessel', 'Large Vessel', 'Cryptogenic', 'Hypercoagulable', 'Structural', 'Cardioembolic')),
    CHECK (AnemiaSeverity IN ('Mild', 'Severe')),
    CHECK (ArterialClotOccurrences IN ('Single prior event', 'Multiple prior events')),
    CHECK (PFOPresence IN ('Positive', 'Negative', 'Unknown')),
    CHECK (VenousClotOccurrences IN ('Single', 'Multiple')),
    CHECK (EjectionFraction IN ('<=40%', '>40%', 'Unknown')),
    CHECK (StenosisPercentage IN ('50-70%', '>70%', 'Unknown')),
    CHECK (OSASeverity IN ('Mild', 'Moderate', 'Severe', 'Unknown')),
    CHECK (CADType IN ('Symptomatic multi or single vessel', 'Asymptomatic multivessel', 'Asymptomatic single vessel', 'Unknown')),
    CHECK (PhysicalInactivityLevel IN ('Mild', 'Moderate', 'Severe')),
    CHECK (LDLLevel IN ('Borderline', 'High', 'Very High', 'Unknown')),
    CHECK (HDLLevel IN ('Low', 'Unknown')),
    CHECK (TriglyceridesLevel IN ('Moderate', 'High', 'Unknown')),
    CHECK (Gender IN ('man', 'woman')),
    UNIQUE KEY unique_response (syntrillo_internal_key_patient, syntrillo_internal_key_clinician, created_at)
);

CREATE TABLE IF NOT EXISTS srs_compliance_records (
    srs_form_response_id INT NOT NULL PRIMARY KEY,
    strokeCompliance VARCHAR(50),
    tiaCompliance VARCHAR(50),
    chronicInfarctCompliance VARCHAR(50),
    atrialFibrillationCompliance VARCHAR(50),
    ironDeficiencyAnemiaCompliance VARCHAR(50),
    arterialClotsCompliance VARCHAR(50),
    venousClotsCompliance VARCHAR(50),
    chfCompliance VARCHAR(50),
    carotidStenosisCompliance VARCHAR(50),
    osaCompliance VARCHAR(50),
    cadCompliance VARCHAR(50),
    valvularHeartDiseaseCompliance VARCHAR(50),
    ckdCompliance VARCHAR(50),
    triglyceridesCompliance VARCHAR(50),
    ldlCompliance VARCHAR(50),
    hdlCompliance VARCHAR(50),
    FOREIGN KEY (srs_form_response_id) REFERENCES srs_form_responses(srs_form_response_id) ON DELETE CASCADE ON UPDATE CASCADE
)

CREATE TABLE IF NOT EXISTS srs_independent_risk_values (
  risk_value_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  category VARCHAR(50) NOT NULL,
  risk_value FLOAT NOT NULL,
  is_default BOOLEAN NOT NULL DEFAULT FALSE,
  min_value FLOAT,
  max_value FLOAT,
  categorical_value VARCHAR(100),
  gender VARCHAR(50)
)