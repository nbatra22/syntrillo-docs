# create a lambda function handler that returns hello
def hello_handler(event, context):
    return {
        'statusCode': 200,
        'body': 'Hello from Lambda!'
    }
