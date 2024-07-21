# Path: ./sources/syntrillo/databases_management/connection.py

import sys
import os
import time
from dotenv import load_dotenv

# modules used to retrieve secrets in aws secrets manager:
import requests
import json

# https://help.pythonanywhere.com/pagesAccessingMySQLFromOutsidePythonAnywhere/

import pymysql
try:
    import sshtunnel  # on PythonAnywhere, requires : pip install sshtunnel

    sshtunnel.SSH_TIMEOUT = 60.0
    sshtunnel.TUNNEL_TIMEOUT = 60.0
except ImportError:
    pass

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

        if os.getenv('AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN') != None:
            # This test means we are in the lambda function
            # We use AWS Secrets Manager to retreive the database secrets
            # TAWS Secrets Manager should be accessible only by the lambda function and/or and admin user

            secret_arn = os.getenv('AWS_SECRETS_MANAGER_DATABASE_SECRET_ARN')

            # This uses the lambda extension layer for secrets and parameters
            # This uses a cache and avoid calling the secrets manager each time (it reduces cost & latency)
            get_secret_value_response = requests.get(
                f"http://localhost:2773/secretsmanager/get?secretId={secret_arn}",
                headers={"X-AWS-Parameters-Secrets-Token": os.environ.get('AWS_SESSION_TOKEN')},
            )

            secret_value = get_secret_value_response.text
            secret_dict = json.loads(secret_value)
            secret_string = secret_dict["SecretString"]

            host=json.loads(secret_string)['host']
            username=json.loads(secret_string)['username']
            password=json.loads(secret_string)['password']

            self.AWS_DB_CONFIG = {
                'host': host,
                'user': username,
                'password': password,
            }

        else:
            # paths have to be hard-coded at PythonAnywhere
            if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_'):
                dotenv_path = '/home/syntrillo/Syntrillo_Clinic/.env'
            else:
                dotenv_path = ".env"

            load_dotenv(dotenv_path=dotenv_path)

            # select database to use
            self.database_server = os.getenv('DATABASE_SERVER')

            if self.database_server == 'AWS':

                self.AWS_DB_CONFIG = {
                    'host': os.getenv('AWS_DATABASE_CONFIG_HOST'),
                    'user': os.getenv('AWS_DATABASE_CONFIG_USER'),
                    'password': os.getenv('AWS_DATABASE_CONFIG_PASSWORD'),
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
            pymysql.connections.Connection: A connection object to the MySQL database if successful, otherwise None.
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
