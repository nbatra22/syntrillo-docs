from http import HTTPStatus

from aws_lambda_powertools.event_handler import (
    APIGatewayRestResolver,
    Response,
    content_types,
)

app = APIGatewayRestResolver()

@app.get("/")
def landing_page():
    landing_page = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Check Functions</title>
      </head>
      <body>
        <h1>Welcome to the "Syntrillo Clinic Backend Check Functions" Landing Page</h1>
        <p>It lists all checks of syntrillo clinic backend on AWS</p>
        <p>Click on the links for more information</p>
        <a href="check/check-database-encryption-details">Check-Database-Encryption Status: </a>{check_database_encryption()["Status"]}
        </br>
        <a href="check/check-database-connection-details">Check-Database-Connection Status: </a>{check_database_connection()["Status"]}
      </body>
    </html>
    """

    return Response(
        status_code=HTTPStatus.OK.value,  # 200
        content_type=content_types.TEXT_HTML,
        body=landing_page,
    )

def check_database_encryption():
    import boto3

    # Create an RDS client
    rds_client = boto3.client('rds')

    # Specify the DB instance identifier
    db_instance_identifier = 'syntrilloclinicbackendsta-mysqldatabasefromsnapsho-pgfocymgbys3'

    # Describe the DB instance
    response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)

    # Check if the DB instance is encrypted
    db_instance = response['DBInstances'][0]
    if db_instance['StorageEncrypted']:
        return { "Status":"OK" , "Info": f"The RDS database instance {db_instance_identifier} is encrypted." }
    else:
        return { "Status":"KO", "Info": f"The RDS database instance {db_instance_identifier} is not encrypted." }

class Database:
    def __init__(self):
        pass

    def get_connection(self):
        db_conn = DatabaseConnection(DatabaseConnection.PSEUDONYM_DB)
        self.conn, self.tunnel = db_conn.create_connection(verbose=True)
        return self.conn
    
    def close_connection(self):
        self.conn.close()

from syntrillo.databases_management.connection import DatabaseConnection

def check_database_connection():
    db = Database()
    connection = db.get_connection()
    if connection:
        db.close_connection()
        return { "Status":"OK" , "Info": f"The RDS database instance is ACCESSIBLE." }
    else:
        return { "Status":"KO" , "Info": f"The RDS database instance is NOT ACCESSIBLE." }

@app.get("/check/check-database-connection-details")
def check_database_connection_details():
    return {"check-database-connection-details": check_database_connection()}

@app.get("/check/check-database-encryption-details")
def check_database_encyption_details():
    return {"check-database-encyption-details": check_database_encryption()}

def handler(event, context):
    return app.resolve(event, context)