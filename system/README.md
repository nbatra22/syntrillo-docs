# SyntrilloClinic - System

Various docs and scripts about systems


## Requirements & Environments

This app was initially developed with Anaconda on PythonAnywhere.

`environement.yml` created with `conda env export --name syntrillo --file environment.yml`

Then, to allow portability to AWS, a 'pip' environement was used instead.

Packages were listed with `extract_imports.py` and manually currated in `imported_packages_manually_curated.txt`


### Install python 3.10 (may be needed for openai)

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

### pip env set-up

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

### pip : generate requirements

```
# Install the necessary packages (based on imported_packages.txt)
pip install -r imported_packages.txt

# Generate the requirements.txt
pipreqs /path/to/your/flask/app

# Alternatively, you can use pip freeze
pip freeze > requirements.txt
```


