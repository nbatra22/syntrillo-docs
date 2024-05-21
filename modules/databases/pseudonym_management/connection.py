# modules/databases/pseudonym_management/connection.py

import sys
import os

# add this folder to system path so that local modules can be imported
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


# Python Anywhere creds
# Database host address: syntrillo.mysql.pythonanywhere-services.com
# Username: syntrillo
# pwd : WbQELeX9nhAkC7jUvfSFyH

# https://help.pythonanywhere.com/pages/AccessingMySQLFromOutsidePythonAnywhere/

# if mysql-connector-python :
#   conda install -c conda-forge mysql-connector-python
#   print("mysql.connector.__version__ : ", mysql.connector.__version__) # verify installation and version
# import mysql-connector : !!! does not work with mysql-connector!!!
import MySQLdb
import sshtunnel

sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0



# TODO : need to move this outside the source code : use dotenv at the top level (.env will be look for )
"""
the load_dotenv() function from the python-dotenv library will automatically search for a .env file in the directory from which the script is executed, and if it doesn't find one there, it will continue searching in parent directories up to the root directory. This behavior allows for flexibility in locating the .env file without hardcoding its path.
"""

DB_CONFIG = {
    'user': 'syntrillo',
    'password': 'WbQELeX9nhAkC7jUvfSFyH',
    'host': 'syntrillo.mysql.pythonanywhere-services.com',
    'database': 'syntrillo$PseudonymManagement',
}


def create_connection(verbose : bool = False):
    try:
        if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_'):
            # No SSH tunnel required for PythonAnywhere
            conn = MySQLdb.connect(**DB_CONFIG)
            if verbose:
                print("_this_is_PythonAnywhere_ : connection to ",  DB_CONFIG.get('database'), " successful.")
            return conn
        else:
            # Create SSH tunnel for local machine
            with sshtunnel.SSHTunnelForwarder(
                    ('ssh.pythonanywhere.com'),
                    ssh_username='syntrillo',
                    ssh_password='zMRGeiv}2D472xg',
                    remote_bind_address=(DB_CONFIG.get('host'), 3306)
            ) as tunnel:
                # Tunnel is established, connect to the MySQL database
                db_config_ssh=DB_CONFIG.copy()
                db_config_ssh['host'] = '127.0.0.1'
                db_config_ssh['port'] = tunnel.local_bind_port
                conn = MySQLdb.connect(**db_config_ssh)
                if verbose:
                    print("remote connection to ",  DB_CONFIG.get('database'), " successful.")
                return conn
    except sshtunnel.BaseSSHTunnelForwarderError as ssh_err:
        print(f"SSH Tunnel Error: {ssh_err}")
    except MySQLdb.Error as mysql_err:
        print(f"MySQL Error: {mysql_err}")
    except Exception as e:
        print(f"Unexpected Error: {e}")
    return None

if __name__ == '__main__':
    create_connection(verbose=True)


