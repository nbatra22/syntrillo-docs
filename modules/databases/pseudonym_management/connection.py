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

# conda install -c conda-forge mysql-connector-python
import mysql.connector

DB_CONFIG = {
    'user': 'syntrillo',
    'password': 'WbQELeX9nhAkC7jUvfSFyH',
    'host': 'syntrillo.mysql.pythonanywhere-services.com',
    'database': 'syntrillo$PseudonymManagement'
}


def create_connection(verbose : bool = False):
    """
    Connection to PseudonymManagement
    """
    try:
        if verbose:
            print("mysql.connector.__version__ : ", mysql.connector.__version__) # verify installation and version
        conn = mysql.connector.connect(**DB_CONFIG)
        if verbose:
            print("connection to ",  DB_CONFIG.get('database'), " successful.")
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


if __name__ == '__main__':
    create_connection(verbose=True)


