# Syntrillo Clinic Repository

`SyntrilloClinic` repository hosted by Syntrillo : https://github.com/Syntrillo/SyntrilloClinic

## Project Overview

This repository contains the Syntrillo Clinic platform, designed to handle multiple applications with shared modules and configurations.

## Directory Structure

TODO : update

```
SyntrilloClinic
|-- apps
|   |-- AWS
|   `-- PythonAnywhere
|       |-- scripts
|       `-- website
|-- sources
|   `-- syntrillo
|       |-- api_healthie
|       |-- api_tenovi
|       |-- data_structures
|       |-- databases_management
|       |-- patient_initialization
|       |-- patient_onboarding
|       |-- pseudonyms_management
|       `-- virtual_care_navigator
|-- tests
`-- system
```

### Directory Descriptions

- **`apps/`**: Contains environment-specific applications:
  - **`AWS/`**: Placeholder for AWS-specific application configurations and scripts.
  - **`PythonAnywhere/`**: Contains the Flask-based web application and related scripts for PythonAnywhere deployment.
    - **`scripts/`**: Contains configuration scripts for the PythonAnywhere environment.
    - **`website/`**: Contains the Flask app files, static assets, and HTML templates.

- **`sources/`**: Contains shared packages, modules and utilities:
  - **`syntrillo/`**: Core functionality and data handling.
    - **`api_healthie/`**: Commnucation with Healthie API.
    - **`api_tenovi/`**:  Communication with Tenovi API.
    - **`data_structures/`**: Storage and management of questionnaires.
    - **`databases_management/`**: Connection to and setting-up of Syntrillo databases.
    - **`patient_initialization/`**: Initialization procedures for patients at Healthie and Tenovi.
    - **`patient_onboarding/`**: Management of patients onboarding procedures at Healthie.
    - **`pseudonyms_management/`**: HIPAA compliant creation, pairing and management of look-up codes (identifiers, keys, pseudonyms). [See its README.md](./sources/syntrillo/pseudonyms_management/README.md)
    - **`virtual_care_navigator/`**: Interface with LLM.

- **`tests/`**: Contains test cases and unittests for various modules and environments.

- **`system/`**: Various scripts to manage the code. [system README.md](./system/README.md)

- **Configuration and Dependencies**:
  - **`env_template.ini`**: Template for environment-specific variables `env.ini` file.
  - **`requirements.txt`**: Python dependencies.

### Usage

1. **Install python dependencies**:
   - Create and activate a virtual python environment. It has been tested with python3.9
   - Install packages listed in `requirements.txt` with 'pip'

```
# Navigate to your python environments
cd /path/to/python_environments/

# Create a new virtual environment
python3.9 -m venv new_env

# Activate the virtual environment
source new_env/bin/activate

# Install dependencies from requirements.txt
cd /path/to/SyntrilloClinicRootFolder/
pip install -r requirements.txt
```

2. **Setup Environment**:
   - Copy `env_template.ini` to `.env` and fill in the required environment variables.

3. **Run Applications**:
   - Navigate to the desired environment directory under `apps/` and follow the instructions in the respective `README.md` files:
       - [AWS Application Documentation README.md](./apps/AWS/README.md)
       - [PythonAnywhere Application Documentation README.md](./apps/PythonAnywhere/README.md)

4. **Run Tests**:
  - Use the `tests/` directory to run unit tests and integration tests for the various modules and applications.


### Misc

Example of saving requirements with pipreqs, ignoring AWS stuff
```bash
pipreqs ./ --ignore ./apps/AWS/ --savepath requirements_v2.txt
```

Move to pymysql:
   - not available on PythonAnywhere `pip show pymysql`, have to install it: `pip install pymysql`
   - installs well on `p3.9_Syntrillo_Clinic_v2` @ maxwell
   - summary of changes:
        - Replaced `import MySQLdb` with `import pymysql`.
        - Updated `MySQLdb.connect` to `pymysql.connect`.
        - Replaced `MySQLdb.Error` with `pymysql.MySQLError`.
        - Replaced `MySQLdb.OperationalError`with `pymysql.OperationalError`

 



