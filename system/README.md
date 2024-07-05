# SyntrilloClinic - System

Various docs and scripts about systems


## Requirements & Environments

This app was initially developed with Anaconda on PythonAnywhere.

`environement.yml` created with `conda env export --name syntrillo --file environment.yml`

Then, to allow portability to AWS, a 'pip' environement was used instead.

Packages were listed with `extract_imports.py` and manually currated in `imported_packages_manually_curated.txt`


### Install python 3.10 (may be needed for openai)

```bash
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

### pip env set-up

```bash
sudo apt install python3.9-venv python3.9-distutils
# in local syntrillo env dedicated folder:
python3.9 -m venv p3.9_env_test
python3.10 -m venv p3.10_env_test
```

```bash
source p3.9_env_test/bin/activate
which python
which pip
pip install pipreqs
```

dependencies on Debian 11:
```bash
# 'pip install mysqlclient' requires
sudo apt install python3.9-dev libmariadb-dev
```

### pip : generate requirements

```bash
# Install the necessary packages (based on imported_packages.txt)
pip install -r imported_packages.txt

# Generate the requirements.txt
pipreqs /path/to/your/flask/app

# Alternatively, you can use pip freeze
pip freeze > requirements.txt
```


Example of saving requirements with pipreqs, ignoring AWS stuff
```bash
pipreqs ./ --ignore ./apps/AWS/ --savepath requirements_v2.txt
```

## Procedure to generate and update a new environment version on Maxwell

### create new version

```bash
# Navigate to your python environments
cd /home/olivier/projects/Syntrillo/python_environments

# Create a new virtual environment
#  : requires   'apt-get install python3-venv'
python3.9 -m venv p3.9_Syntrillo_Clinic_v3

# Activate the virtual environment
#  : gives : "(p3.9_Syntrillo_Clinic_v3) /home/olivier/projects/Syntrillo/python_environments"
source p3.9_Syntrillo_Clinic_v3/bin/activate

# Install dependencies from requirements.txt in SyntrilloClinic
#  ( may need to update requirements.txt first with pipreqs )
cd /home/olivier/projects/Syntrillo/Syntrillo_Clinic
pip install -r requirements.txt
```

### install new packages in new version

```bash
# Navigate to your python environments
cd /home/olivier/projects/Syntrillo/python_environments

# Activate the virtual environment
source p3.9_Syntrillo_Clinic_v3/bin/activate

pip install pandas numpy matplotlib
```

### create new requirements file

with pipreqs, ignoring AWS stuff
```bash
source p3.9_Syntrillo_Clinic_v2/bin/activate
pip install pipreqs
cd /home/olivier/projects/Syntrillo/Syntrillo_Clinic
pipreqs ./ --ignore ./apps/AWS/ --savepath requirements_v3.txt
```

