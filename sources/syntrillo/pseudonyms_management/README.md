# Pseudonyms Management

This repository contains two Python scripts essential for managing pseudonymization of health information in accordance with HIPAA Safe Harbor rules. These scripts ensure the secure handling and management of protected health information (PHI) by using pseudonyms, thus enhancing privacy and compliance with regulatory standards.

## Files

### 1. `lookup_codes_management.py`

This script defines the `LookUpCodesManagement` class, responsible for managing look-up codes in the Syntrillo database. Each entry links a healthy user ID to an internal key and a pseudonym for accessing PHI.

#### Key Features:
- **Create Entries**: Adds new entries linking healthy user IDs to internal keys and pseudonyms.
- **Retrieve Entries**: Allows retrieval of entries using healthy user IDs, internal keys, or pseudonyms.
- **Close Connections**: Safely closes database connections and SSH tunnels.

#### Regulatory Objective:
The primary regulatory objective of this script is to comply with HIPAA's Safe Harbor rules by ensuring that PHI is accessed and managed using pseudonyms. This reduces the risk of unauthorized access and enhances the privacy of health information.

#### Methods:
- `create_entry(healthy_user_id)`: Creates a new entry for a healthy user ID.
- `retrieve_entry_by_healthy_user_id(healthy_user_id)`: Retrieves an entry using the healthy user ID.
- `retrieve_entry_by_internal_key(internal_key)`: Retrieves an entry using the internal key.
- `retrieve_entry_by_pseudo_code(pseudo_code)`: Retrieves an entry using the pseudonym.
- `close_connection()`: Closes the database connection.

### 2. `temporary_lookup_codes_management.py`

This script defines the `TemporaryLookUpCodesManagement` class, responsible for managing temporary look-up codes. It supports the creation and management of temporary pseudonyms for different purposes, including identifying iFrames and Tenovi devices.

#### Key Features:
- **Generate Temporary Codes**: Creates UUIDs or random word pairs as temporary codes.
- **Retrieve and Delete Entries**: Retrieves internal keys using temporary codes and deletes old entries or specific entries based on their temporary codes.
- **Logging**: Adds detailed log entries for all significant actions, ensuring traceability and compliance.

#### Regulatory Objective:
The script's main regulatory goal is to ensure compliance with HIPAA's Safe Harbor rules by using temporary pseudonyms for PHI access. This minimizes the risk of re-identification and safeguards patient privacy during temporary data access operations.

#### Methods:
- `generate_uuid_code()`: Generates a random UUID string.
- `generate_word_code()`: Generates a random string of two capitalized words.
- `create_temporary_pseudo_code(syntrillo_internal_key, purpose)`: Creates a temporary pseudonym for a given internal key and purpose.
- `retrieve_syntrillo_internal_key(temp_code, purpose)`: Retrieves the internal key using a temporary code.
- `delete_entry(temp_code, purpose)`: Deletes an entry using the temporary code and purpose.
- `delete_old_entries()`: Deletes entries older than 24 hours.

### Example Usage
Both scripts include example usage sections demonstrating how to instantiate the management classes, create temporary codes, retrieve internal keys, and delete old entries.

### Conclusion
These scripts are crucial for maintaining HIPAA compliance by managing PHI through pseudonyms. They offer robust methods for creating, retrieving, and managing pseudonymized data, thereby enhancing privacy and security in healthcare data management.

For further details on implementation and usage, please refer to the docstrings within each script.
