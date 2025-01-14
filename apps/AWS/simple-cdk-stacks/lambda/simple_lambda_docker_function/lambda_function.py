# import chromadb
from chromadb import PersistentClient

def simple_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!#!'
    }
