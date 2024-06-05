#!/bin/bash

# This script is used to create an SSH tunnel to the MySQL database on PythonAnywhere
# Works with SQLTools extension in VSCode, see JSON connection string at the end of this script
# Best to run this script outside of VSCode terminal, so that other scripts can be run in VSCode terminal

# make sure we are in the directory of this script
cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")";

source ../.env

# echo ${PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_USERNAME}
# echo ${PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_PASSWORD}

sshpass -p "${PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_PASSWORD}" \
   ssh -N -L 3366:syntrillo.mysql.pythonanywhere-services.com:3306 ${PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_USERNAME}@ssh.pythonanywhere.com


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