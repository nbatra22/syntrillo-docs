# SyntrilloClinic Development Repository

`SyntrilloClinic` repository hosted by Syntrillo : https://github.com/Syntrillo/SyntrilloClinic

## Project Overview

This repository contains the Syntrillo Clinic platform, designed to handle multiple applications with shared modules and configurations. The structure ensures modularity, clarity, and ease of development for various environments, including AWS and PythonAnywhere.

## Directory Structure

```
SyntrilloClinic
|-- apps
|   |-- AWS
|   `-- PythonAnywhere
|       |-- scripts
|       `-- website
|-- sources
|   `-- syntrillo
|       |-- data
|       |-- databases
|       `-- healthie
`-- tests
    |-- databases
    `-- healthie

```

Sources structure to consider
```
- databases_management
- healthie_api
- tenovi_api
- llm_api

- pseudo_code_manager
- accounts_pairing
- onboarding_manager
- virtual_care_navigator

```



### Directory Descriptions

- **`apps/`**: Contains environment-specific applications:
  - **`AWS/`**: Placeholder for AWS-specific application configurations and scripts.
  - **`PythonAnywhere/`**: Contains the Flask-based web application and related scripts for PythonAnywhere deployment.
    - **`scripts/`**: Contains configuration scripts for the PythonAnywhere environment.
    - **`website/`**: Contains the Flask app files, static assets, and HTML templates.

- **`sources/`**: Contains shared packages, modules and utilities:
  - **`syntrillo/`**: Core functionality and data handling.
    - **`data/`**: Data structures and storage management.
    - **`databases/`**: Database connection and management modules.
    - **`healthie/`**: Healthie integration and related utilities.

- **`tests/`**: Contains test cases for various modules and environments:
  - **`databases/`**: Tests for database connections.
  - **`healthie/`**: Tests for Healthie integration, separated by production and staging environments.

- **Configuration and Dependencies**:
  - **`env_template.ini`**: Template for environment-specific variables.
  - **`environment.yml`**: Conda environment configuration.
  - **`requirements.txt`**: Python dependencies.

### Usage

1. **Setup Environment**:
   - Copy `env_template.ini` to `.env` and fill in the required environment variables.
   - Create and activate the Conda environment using `environment.yml`.

2. **Run Applications**:
   - Navigate to the desired environment directory under `apps/` and follow the instructions in the respective `README.md` files.

3. **Run Tests**:
   - Use the `tests/` directory to run unit tests and integration tests for the various modules and applications.

This structure ensures modularity and clear separation of concerns, making it easier to manage and develop the Syntrillo Clinic platform.


## Installation of python packages


```
# Navigate to the project env directory
cd /path/to/project_env

# Create a new virtual environment
python3.9 -m venv new_env

# Activate the virtual environment
source new_env/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

## Installation on PythonAnywhere

```
   - making use of python 3.9 everywhere : set-up in System Image
   - need to 'pip3.9 install statsmodels markdown2' in the console.
      :Make sure to use the right python version !!!
      : see : https://help.pythonanywhere.com/pages/InstallingNewModules/
```

## Run and debug Flask app locally

```
  : in VSCode terminal : flask --app ./flask_app.py run

  : run > Start Debugging  (using .vscode/launch.json ) see : https://code.visualstudio.com/docs/python/tutorial-flask
```


