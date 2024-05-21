# modules/databases/pseudonym_management/connection.py

import sys
import os
from dotenv import load_dotenv

# https://help.pythonanywhere.com/pages/AccessingMySQLFromOutsidePythonAnywhere/

# if mysql-connector-python :
#   conda install -c conda-forge mysql-connector-python
#   print("mysql.connector.__version__ : ", mysql.connector.__version__) # verify installation and version
# import mysql-connector : !!! does not work with mysql-connector!!!
import MySQLdb
import sshtunnel

sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0

load_dotenv(dotenv_path=".env.PA-databases")

PA_DB_CONFIG = {
    'user': os.getenv('PA_DB_CONFIG_USER'),
    'password': os.getenv('PA_DB_CONFIG_PASSWORD'),
    'host': os.getenv('PA_DB_CONFIG_HOST'),
    'database': os.getenv('PA_DB_CONFIG_DATABASE'),
}

PA_SSH_TUNNEL = {
    'ssh_username': os.getenv('PA_DB_CONFIG_SSH_USERNAME'),
    'ssh_password': os.getenv('PA_DB_CONFIG_SSH_PASSWORD'),
}

def create_connection(verbose : bool = False):
    try:
        if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_'):
            # No SSH tunnel required if running inside PythonAnywhere cloud
            conn = MySQLdb.connect(**PA_DB_CONFIG)
            if verbose:
                print("_this_is_PythonAnywhere_ : connection to ",  PA_DB_CONFIG.get('database'), " successful.")
            return conn
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
                conn = MySQLdb.connect(**db_config_ssh)
                if verbose:
                    print("remote connection to ",  PA_DB_CONFIG.get('database'), " successful.")
                return conn
    except sshtunnel.BaseSSHTunnelForwarderError as ssh_err:
        print(f"SSH Tunnel Error: {ssh_err}")
    except MySQLdb.Error as mysql_err:
        print(f"MySQL Error: {mysql_err}")
    except Exception as e:
        print(f"Unexpected Error: {e}")
    return None

if __name__ == '__main__':
    conn = create_connection(verbose=True)
    if conn:
            conn.close()


