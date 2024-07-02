def handler(event, context):
    return {
        'statusCode': 200,
        'body': f"SYNTRILLO CLINIC BACKEND PROD API - {event['path']}"
    }