DROP TABLE IF EXISTS user_look_up_codes;
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

DROP TABLE IF EXISTS user_look_up_temporary_codes;
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