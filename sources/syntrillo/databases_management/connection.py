# Path: ./sources/syntrillo/databases_management/connection.py

import sys
import os
import time
from dotenv import load_dotenv

# https://help.pythonanywhere.com/pagesAccessingMySQLFromOutsidePythonAnywhere/

import pymysql
try:
    import sshtunnel  # on PythonAnywhere, requires : pip install sshtunnel

    sshtunnel.SSH_TIMEOUT = 60.0
    sshtunnel.TUNNEL_TIMEOUT = 60.0
except ImportError:
    pass

from syntrillo.system.local_environment_and_secrets import LocalEnvironmentAndSecrets

class DatabaseConnection:
    """
    A class to manage connections to different databases in the Syntrillo system.

    The Syntrillo system utilizes multiple databases for various purposes, including pseudonym management and health information storage. These databases play a crucial role in ensuring compliance with HIPAA regulations by pseudonymizing and securely storing sensitive patient data.

    The objectives of each database in the context of HIPAA regulations are as follows, these are not implemented in the PythonAnywhere version of the code:

    PSEUDONYM_DB (syntrillo$PseudonymManagement):
    - Store pseudonymized user data to maintain compliance with HIPAA safe harbor regulations.
    - Generate and manage internal identifiers linking records across platforms to facilitate re-identification when necessary.
    - Ensure that pseudonyms and codes are generated programmatically via secure API calls, triggered automatically by specific events, to prevent unauthorized access.
    - Implement strict access controls to restrict access to the lookup table containing re-identification codes, allowing only authorized personnel to access the data.

    HEALTH_INFO_DB (syntrillo$HealthInformation):
    - Store health information data securely while maintaining the privacy of participants.
    - Utilize robust encryption methods for data at rest and in transit to safeguard patient data.
    - Ensure that only authorized personnel have access to sensitive health information stored in the database.
    """
    PSEUDONYM_DB = 'syntrillo$PseudonymManagement'
    HEALTH_INFO_DB = 'syntrillo$HealthInformation'

    def __init__(self, database_name):
        self.database_name = database_name
        self.conn = None
        self.tunnel = None

    def select_database_and_load_credentials(self):
        """
        Load database credentials based on environment variables stored in a .env file

        Returns:
            tuple: A tuple containing two dictionaries:
                - PA_DB_CONFIG: Database configuration parameters.
                - PA_SSH_TUNNEL: SSH tunnel configuration parameters.
        """

        # ------------------------------
        # load aws databases secrets
        env_secrets = LocalEnvironmentAndSecrets(load_aws_database_secrets=True)

        # ------------------------------
        if env_secrets.is_lambda():
            # we are in the lambda function, and we use the AWS database
            self.AWS_DB_CONFIG = {
                'host': env_secrets.get_aws_database_host(),
                'user': env_secrets.get_aws_database_user(),
                'password': env_secrets.get_aws_database_password(),
                'ssl_ca': 'syntrillo/system/rds-certificate-bundle/us-east-1-bundle.pem',
            }

        else:
            # we are not in the lambda function, the dotenv file is used to define the database configuration

            # select database to use
            self.database_server = os.getenv('DATABASE_SERVER')
            if self.database_server == 'AWS':

                self.AWS_DB_CONFIG = {
                    'host': env_secrets.get_aws_database_host(),
                    'user': env_secrets.get_aws_database_user(),
                    'password': env_secrets.get_aws_database_password(),
                    'port': int(env_secrets.get_aws_database_local_port()),
                    'ssl': {'ssl': True}  # Enforce SSL
                }

            elif self.database_server == 'PythonAnywhere':
                self.PA_DB_CONFIG = {
                    'user': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_USER'),
                    'password': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_PASSWORD'),
                    'host': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_HOST'),
                }

                self.PA_SSH_TUNNEL = {
                    'ssh_username': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_USERNAME'),
                    'ssh_password': os.getenv('PYTHON_ANYWHERE_DATABASE_CONFIG_SSH_PASSWORD'),
                }
            else:
                raise ValueError("Invalid database server configuration")


    def create_connection(self, verbose=False, retries=3, delay=5):
        """
        Creates a connection to the MySQL database. It either connects directly if running on PythonAnywhere, or establishes an SSH tunnel if running locally.

        Args:
            verbose (bool): If True, prints connection status messages.
            retries (int): Number of retry attempts if connection fails.
            delay (int): Delay in seconds between retry attempts.

        Returns:
            tuple (pymysql.connections.Connection, sshtunnel.SSHTunnelForwarder): A tuple containing two objects: i) A connection object to the MySQL database if successful, otherwise None. ii) An SSH tunnel object to ssh.pythonanywhere.com if required and successful, otherwise None.
        """

        self.select_database_and_load_credentials()

        if os.getenv('AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN') != None or self.database_server == 'AWS':
            aws_db_config = self.AWS_DB_CONFIG

            # update with requested database name
            aws_db_config['database'] = self.database_name

            self.conn = pymysql.connect(**aws_db_config)
            if verbose:
                print("connection to", aws_db_config.get('host'), "successful.")
            return self.conn, None

        elif self.database_server == 'PythonAnywhere':

            pa_db_config = self.PA_DB_CONFIG
            ps_ssh_tunnel = self.PA_SSH_TUNNEL

            attempt = 0

            # update with requested database name
            pa_db_config['database'] = self.database_name

            while attempt < retries:
                try:
                    if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_'):
                        # No SSH tunnel required if running inside PythonAnywhere platform
                        self.conn = pymysql.connect(**pa_db_config)
                        if verbose:
                            print("_this_is_PythonAnywhere_: connection to", pa_db_config.get('database'), "successful.")
                        return self.conn, None
                    else:
                        # Create SSH tunnel for local machine
                        self.tunnel = sshtunnel.SSHTunnelForwarder(
                            ('ssh.pythonanywhere.com'),
                            ssh_username=ps_ssh_tunnel.get('ssh_username'),
                            ssh_password=ps_ssh_tunnel.get('ssh_password'),
                            remote_bind_address=(pa_db_config.get('host'), 3306),
                            allow_agent=False,  # prevents usage of ssh agents and .ssh/config
                        )
                        self.tunnel.start()
                        # Tunnel is established, connect to the MySQL database
                        db_config_ssh = pa_db_config.copy()
                        db_config_ssh['host'] = '127.0.0.1'
                        db_config_ssh['port'] = self.tunnel.local_bind_port
                        self.conn = pymysql.connect(**db_config_ssh)
                        if verbose:
                            print("remote connection to", pa_db_config.get('database'), "successful.")
                        return self.conn, self.tunnel

                except sshtunnel.BaseSSHTunnelForwarderError as ssh_err:
                    print(f"SSH Tunnel Error: {ssh_err}")
                except pymysql.MySQLError as mysql_err:
                    print(f"MySQL Error: {mysql_err}")
                except Exception as e:
                    print(f"Unexpected Error: {e}")

                attempt += 1
                if attempt < retries:
                    print(f"Retrying in {delay} seconds... ({attempt}/{retries})")
                    time.sleep(delay)

        else:
            print("Invalid database server configuration")

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
