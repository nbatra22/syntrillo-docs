#!/bin/bash

# This script is used to create an SSH tunnel to the MySQL database on PythonAnywhere
# Works with SQLTools extension in VSCode, see JSON connection string at the end of this script
# Best to run this script outside of VSCode terminal, so that other scripts can be run in VSCode terminal

# make sure we are in the directory of this script
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")";

source ../.env

# echo ${PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_USERNAME}
# echo ${PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_PASSWORD}

read -p "Enter the LOCAL_PORT (default: 3366): " LOCAL_PORT
LOCAL_PORT=${LOCAL_PORT:-3366}

echo
echo "If tunnel successful, in a new terminal, connect with:"
echo "   mysql -h 127.0.0.1 --port ${LOCAL_PORT} -u syntrillo --password='xxxxxxxxxxx'"
echo

sshpass -p "${PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_PASSWORD}" \
   ssh -o TCPKeepAlive=no -o ServerAliveInterval=15 -N -L ${LOCAL_PORT}:syntrillo.mysql.pythonanywhere-services.com:3306 ${PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_USERNAME}@ssh.pythonanywhere.com


# VSCode SQLtool JSON connection string
: '
    {
    "mysqlOptions": {
        "authProtocol": "default",
        "enableSsl": "Disabled"
    },
    "previewLimit": 50,
    "server": "127.0.0.1",
    "port": 3366,
    "driver": "MySQL",
    "name": "SyntrilloPythonAnywhere",
    "username": "syntrillo",
    "password": "xxxxxxxxxxxxxxx",
    "database": "syntrillo$PseudonymManagement",
    "connectionTimeout": 600
    }
'
