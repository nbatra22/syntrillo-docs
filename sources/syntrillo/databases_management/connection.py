# Path: ./sources/syntrillo/databases_management/connection.py

import sys
import os
import time
from dotenv import load_dotenv

# https://help.pythonanywhere.com/pagesAccessingMySQLFromOutsidePythonAnywhere/

# if mysql-connector-python :
#   conda install -c conda-forge mysql-connector-python
#   print("mysql.connector.__version__ : ", mysql.connector.__version__) # verify installation and version
# import mysql-connector : !!! does not work with mysql-connector!!!
import MySQLdb
import sshtunnel  # on PythonAnywhere, requires : pip install sshtunnel

sshtunnel.SSH_TIMEOUT = 60.0
sshtunnel.TUNNEL_TIMEOUT = 60.0


class DatabaseConnection:
    PSEUDONYM_DB = 'syntrillo$PseudonymManagement'
    HEALTH_INFO_DB = 'syntrillo$HealthInformation'

    def __init__(self, database_name):
        self.database_name = database_name
        self.conn = None
        self.tunnel = None

    @staticmethod
    def load_database_credentials(dotenv_path=".env"):
        """
        Load database credentials from .env file.

        Returns:
            tuple: A tuple containing two dictionaries:
                - PA_DB_CONFIG: Database configuration parameters.
                - PA_SSH_TUNNEL: SSH tunnel configuration parameters.
        """

        # paths have to be hard-coded at PythonAnywhere
        if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_') and dotenv_path == ".env":
            dotenv_path = '/home/syntrillo/Syntrillo_Clinic/.env'

        load_dotenv(dotenv_path=dotenv_path)

        PA_DB_CONFIG = {
            'user': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_USER'),
            'password': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_PASSWORD'),
            'host': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_HOST'),
        }

        PA_SSH_TUNNEL = {
            'ssh_username': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_USERNAME'),
            'ssh_password': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_PASSWORD'),
        }

        return PA_DB_CONFIG, PA_SSH_TUNNEL

    def create_connection(self, verbose=False, retries=3, delay=5):
        """
        Creates a connection to the MySQL database. It either connects directly if running on PythonAnywhere, or establishes an SSH tunnel if running locally.

        Args:
            verbose (bool): If True, prints connection status messages.
            retries (int): Number of retry attempts if connection fails.
            delay (int): Delay in seconds between retry attempts.

        Returns:
            MySQLdb.connections.Connection: A connection object to the MySQL database if successful, otherwise None.
        """
        PA_DB_CONFIG, PA_SSH_TUNNEL = self.load_database_credentials()
        attempt = 0

        # update with requested database name
        PA_DB_CONFIG['database'] = self.database_name

        while attempt < retries:
            try:
                if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_'):
                    # No SSH tunnel required if running inside PythonAnywhere platform
                    self.conn = MySQLdb.connect(**PA_DB_CONFIG)
                    if verbose:
                        print("_this_is_PythonAnywhere_: connection to", PA_DB_CONFIG.get('database'), "successful.")
                    return self.conn, None
                else:
                    # Create SSH tunnel for local machine
                    self.tunnel = sshtunnel.SSHTunnelForwarder(
                        ('ssh.pythonanywhere.com'),
                        ssh_username=PA_SSH_TUNNEL.get('ssh_username'),
                        ssh_password=PA_SSH_TUNNEL.get('ssh_password'),
                        remote_bind_address=(PA_DB_CONFIG.get('host'), 3306),
                        allow_agent=False,  # prevents usage of ssh agents and .ssh/config
                    )
                    self.tunnel.start()
                    # Tunnel is established, connect to the MySQL database
                    db_config_ssh = PA_DB_CONFIG.copy()
                    db_config_ssh['host'] = '127.0.0.1'
                    db_config_ssh['port'] = self.tunnel.local_bind_port
                    self.conn = MySQLdb.connect(**db_config_ssh)
                    if verbose:
                        print("remote connection to", PA_DB_CONFIG.get('database'), "successful.")
                    return self.conn, self.tunnel

            except sshtunnel.BaseSSHTunnelForwarderError as ssh_err:
                print(f"SSH Tunnel Error: {ssh_err}")
            except MySQLdb.Error as mysql_err:
                print(f"MySQL Error: {mysql_err}")
            except Exception as e:
                print(f"Unexpected Error: {e}")

            attempt += 1
            if attempt < retries:
                print(f"Retrying in {delay} seconds... ({attempt}/{retries})")
                time.sleep(delay)

        return None, None

    def close_connection(self):
        if self.conn:
            self.conn.close()
        if self.tunnel:
            self.tunnel.stop()

# Testing the connection to both databases
if __name__ == '__main__':
    for db_name in [DatabaseConnection.PSEUDONYM_DB, DatabaseConnection.HEALTH_INFO_DB]:
        print(f"Testing connection to {db_name}")
        db_conn = DatabaseConnection(database_name=db_name)
        conn, _ = db_conn.create_connection(verbose=True)
        if conn:
            print(f"Connection to {db_name} Successful")
            db_conn.close_connection()
        else:
            print(f"Connection to {db_name} Unsuccessful")
            sys.exit(1)
