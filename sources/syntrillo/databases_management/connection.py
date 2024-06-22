# Path: ./sources/syntrillo/databases_management/connection.py

import sys
import os
import time
import pymysql

class DatabaseConnection:
    PSEUDONYM_DB = 'syntrillo$PseudonymManagement'
    HEALTH_INFO_DB = 'syntrillo$HealthInformation'

    def __init__(self, database_name):
        self.database_name = database_name
        self.conn = None
        self.tunnel = None

    @staticmethod
    def load_database_credentials(dotenv_path=".env"):
        return None, None

    def create_connection(self, verbose=False, retries=3, delay=5):
        self.connection = pymysql.connect(host='syntrilloclinicbackendstack-mysqldatabase22bdac80-zt8ez017ewyk.cf60aoaem0ky.us-east-1.rds.amazonaws.com' , user='admin', passwd='Sqt8wlAss7UpE7A-86xWR-5ltPXfB.', db=self.database_name) 
        # self.connection = pymysql.connect(host='localhost' , user='olivier', passwd='olivier', db=self.database_name) 
        return self.connection, None

    def close_connection(self):
        if self.conn:
            self.conn.close()
        if self.tunnel:
            self.tunnel.stop()