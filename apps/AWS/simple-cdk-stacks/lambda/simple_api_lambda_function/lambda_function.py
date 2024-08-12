# create a lambda function handler that returns hello
def simple_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!#!'
    }
