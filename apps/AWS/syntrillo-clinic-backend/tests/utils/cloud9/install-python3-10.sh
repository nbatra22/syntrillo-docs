#!/bin/bash

# Update the package manager
sudo yum update -y

# Install the required dependencies
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel

# Download and extract Python 3.10
wget https://www.python.org/ftp/python/3.10.11/Python-3.10.11.tgz
tar xzf Python-3.10.11.tgz

# Compile and install Python 3.10
cd Python-3.10.11
./configure --enable-optimizations
make -j 4
sudo make altinstall

# Set Python 3.10 as the default Python version
sudo alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.10 50
sudo alternatives --config python3

# Verify the installation
/usr/local/bin/python3.10 --version
python3 --version

rm -r Python-3.10.11.*