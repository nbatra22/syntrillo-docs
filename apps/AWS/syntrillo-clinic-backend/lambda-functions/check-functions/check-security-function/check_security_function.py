
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
        <p>It lists all security checks of syntrillo clinic backend on AWS</p>
        <p>Click on the links for more information</p>
        <a href="check-security/check-database-encryption">Check-Database-Encryption: </a>{check_database_encryption_data()["Status"]}
      </body>
    </html>
    """

    return Response(
        status_code=HTTPStatus.OK.value,  # 200
        content_type=content_types.TEXT_HTML,
        body=landing_page,
    )

def check_database_encryption_data():
    import boto3

    # Create an RDS client
    rds_client = boto3.client('rds')

    # Specify the DB instance identifier
    db_instance_identifier = 'syntrilloclinicbackendstackd-mysqldatabase22bdac80-5kt0pwavmcmm'

    # Describe the DB instance
    response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)

    # Check if the DB instance is encrypted
    db_instance = response['DBInstances'][0]
    if db_instance['StorageEncrypted']:
        return { "Status":"OK" , "Info": f"The RDS database instance {db_instance_identifier} is encrypted." }
    else:
        return { "Status":"KO", "Info": f"The RDS database instance {db_instance_identifier} is not encrypted." }

@app.get("/check-security/check-database-encryption")
def check_database_encyption():
    return {"check-database": check_database_encryption_data()}

def handler(event, context):
    return app.resolve(event, context)