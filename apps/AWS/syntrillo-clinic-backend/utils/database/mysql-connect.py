import boto3
import json
import pymysql

def get_secret():
    secret_name = "DatabaseAdminSecrets4B85717-UlIzzA9DkHCH"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        raise e

    # Decrypts secret using the associated KMS key
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

def connect_to_database():
    # Get the secret
    secret = get_secret()

    # Extract the database connection details
    host = secret['host']
    user = secret['username']
    password = secret['password']
    database = secret.get('dbname', '')  # Use 'dbname' if it exists, otherwise empty string

    try:
        # Establish a database connection
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            cursorclass=pymysql.cursors.DictCursor,
            ssl={'ssl': True}
        )

        print("Successfully connected to the database!")

        # Example: Execute a simple query
        with connection.cursor() as cursor:
            sql = "SELECT VERSION()"
            cursor.execute(sql)
            result = cursor.fetchone()
            print(f"Database version: {result['VERSION()']}")

    except Exception as e:
        print(f"Error connecting to the database: {e}")

    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    connect_to_database()