

# local tests

import sys
import os
import time
from dotenv import load_dotenv

# https://help.pythonanywhere.com/pages/AccessingMySQLFromOutsidePythonAnywhere/

import mysql.connector
import sshtunnel

sshtunnel.SSH_TIMEOUT = 30.0
sshtunnel.TUNNEL_TIMEOUT = 30.0
sshtunnel.DEFAULT_LOGLEVEL = 'DEBUG'


dotenv_path = '/home/syntrillo/Syntrillo_Clinic/.env'

load_dotenv(dotenv_path=dotenv_path)

PA_DB_CONFIG = {
    'user': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_USER'),
    'password': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_PASSWORD'),
    'host': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_HOST'),
    'database': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_DATABASE'),
}

PA_SSH_TUNNEL = {
    'ssh_username': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_USERNAME'),
    'ssh_password': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_PASSWORD'),
}


if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_'):
    # No SSH tunnel required if running inside PythonAnywhere platform
    conn = mysql.connector.connect(**PA_DB_CONFIG)
    print("_this_is_PythonAnywhere_ : connection to ",  PA_DB_CONFIG.get('database'), " successful.")
else:
    # Create SSH tunnel for local machine
    with sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username=PA_SSH_TUNNEL.get('ssh_username'),
            ssh_password=PA_SSH_TUNNEL.get('ssh_password'),
            remote_bind_address=(PA_DB_CONFIG.get('host'), 3306)
    ) as tunnel:
        # Tunnel is established, connect to the MySQL database
        db_config_ssh=PA_DB_CONFIG.copy()
        db_config_ssh['host'] = '127.0.0.1'
        db_config_ssh['port'] = tunnel.local_bind_port
        conn = mysql.connector.connect(**db_config_ssh)
        print("remote connection to ",  PA_DB_CONFIG.get('database'), " successful.")

if conn.is_connected():
    print("Connection Successful")
    conn.close()
else:
    print("Connection Unsuccessful")
    sys.exit(1)

