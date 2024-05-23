# ./Syntrillo_Clinic/sources/syntrillo/databases/pseudonym_management/connection.py

import sys
import os
from dotenv import load_dotenv

# https://help.pythonanywhere.com/pagesAccessingMySQLFromOutsidePythonAnywhere/

# if mysql-connector-python :
#   conda install -c conda-forge mysql-connector-python
#   print("mysql.connector.__version__ : ", mysql.connector.__version__) # verify installation and version
# import mysql-connector : !!! does not work with mysql-connector!!!
import MySQLdb
import sshtunnel

sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0

def load_database_credentials():
    """
    Load database credentials from .env file.

    Returns:
        tuple: A tuple containing two dictionaries:
            - PA_DB_CONFIG: Database configuration parameters.
            - PA_SSH_TUNNEL: SSH tunnel configuration parameters.
    """
    load_dotenv(dotenv_path=".env")

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

    return PA_DB_CONFIG, PA_SSH_TUNNEL

def create_connection(verbose : bool = False):
    """
    Creates a connection to the MySQL database. It either connects directly if running on PythonAnywhere, or establishes an SSH tunnel if running locally.

    Args:
        verbose (bool): If True, prints connection status messages.

    Returns:
        MySQLdb.connections.Connection: A connection object to the MySQL database if successful, otherwise None.

    """
    PA_DB_CONFIG, PA_SSH_TUNNEL = load_database_credentials()
    try:
        if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_'):
            # No SSH tunnel required if running inside PythonAnywhere platform
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
        print("Connection Successful")
        conn.close()
    else:
        print("Connection Unsuccessful")
        sys.exit(1)


