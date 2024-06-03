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


### Requirements & Environments

Locally, using anaconda development environment, named 'syntrillo'

`requirement.txt` created & updated manually

`environement.yml` created with `conda env export --name syntrillo --file environment.yml`

#### work in progress : moving to pip

##### Install python 3.10 (needed for openai ?)

```
# install from source on Debian 11
# https://computingforgeeks.com/how-to-install-python-on-debian-linux/
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev
wget https://www.python.org/ftp/python/3.10.14/Python-3.10.14.tgz
tar -xf Python-3.10.*.tgz
cd Python-3.10.14
./configure --prefix=/usr/local --enable-optimizations --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
make -j 4
sudo make altinstall
```

##### pip env set-up

```
sudo apt install python3.9-venv python3.9-distutils
# in local syntrillo env dedicated folder:
python3.9 -m venv p3.9_env_test
python3.10 -m venv p3.10_env_test
```

```
source p3.9_env_test/bin/activate
which python
which pip
pip install pipreqs
```

dependencies on Debian 11:
```
# 'pip install mysqlclient' requires
sudo apt install python3.9-dev libmariadb-dev


```




