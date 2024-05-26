

# local tests

import sys
import os
import time
from dotenv import load_dotenv

# https://help.pythonanywhere.com/pages/AccessingMySQLFromOutsidePythonAnywhere/

import MySQLdb
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

def create_connection():
    if os.path.exists('/home/syntrillo/_this_is_PythonAnywhere_'):
        # No SSH tunnel required if running inside PythonAnywhere platform
        conn = MySQLdb.connect(**PA_DB_CONFIG)
        print("_this_is_PythonAnywhere_ : connection to ",  PA_DB_CONFIG.get('database'), " successful.")
        return conn, None
    else:
        # Create SSH tunnel for local machine
        tunnel = sshtunnel.SSHTunnelForwarder(
                ('ssh.pythonanywhere.com'),
                ssh_username=PA_SSH_TUNNEL.get('ssh_username'),
                ssh_password=PA_SSH_TUNNEL.get('ssh_password'),
                remote_bind_address=(PA_DB_CONFIG.get('host'), 3306),
                allow_agent=False,
        )
        tunnel.start()

        # Tunnel is established, connect to the MySQL database
        db_config_ssh=PA_DB_CONFIG.copy()
        db_config_ssh['host'] = '127.0.0.1'
        db_config_ssh['port'] = tunnel.local_bind_port
        conn = MySQLdb.connect(**db_config_ssh)
        print("remote connection to ",  PA_DB_CONFIG.get('database'), " successful.")
        return conn, tunnel

conn, tunnel = create_connection()

if conn is not None:
    print("Connection Successful")
else:
    print("Connection Unsuccessful")
    sys.exit(1)

# Making Cursor Object For Query Execution
cursor = conn.cursor()

# Create temporary table
create_table_query = "CREATE TABLE temp_table (id INT, name VARCHAR(255))"
cursor.execute(create_table_query)

# Add data to temporary table
insert_data_query = "INSERT INTO temp_table (id, name) VALUES (1, 'John'), (2, 'Jane'), (3, 'Bob')"
cursor.execute(insert_data_query)

# Select and print all data from temporary table
select_data_query = "SELECT * FROM temp_table"
cursor.execute(select_data_query)
result = cursor.fetchall()
for row in result:
    print(row)

# Drop temporary table
drop_table_query = "DROP TABLE temp_table"
cursor.execute(drop_table_query)

conn.close()
tunnel.stop() if tunnel else None
print("Connection Closed")

