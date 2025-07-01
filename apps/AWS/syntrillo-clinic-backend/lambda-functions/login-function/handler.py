import json
import boto3
import os
from botocore.exceptions import ClientError

import base64

def handler(event, context):
    """Login Lambda function - handles user authentication"""

    print('LOGIN EVENT: ', event)

    # Handle different endpoints
    resource = event.get('resource', '')
    http_method = event.get('httpMethod', '')

    # Handle reset password endpoint
    if resource == '/auth/reset-password' and http_method == 'POST':
        return handle_reset_password(event)

    # Handle forgot password endpoint
    if resource == '/auth/forgot-password' and http_method == 'POST':
        return handle_forgot_password(event)

    try:
        # Parse request body
        # body = json.loads(event.get('body', '{}'))
        body = decode_payload(event.get('body', {}))
        username = body.get('username')
        password = body.get('password')
        
        if not username or not password:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Username and password required'})
            }
        
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp')
        
        # Authenticate user
        response = cognito_client.initiate_auth(
            ClientId=os.environ['CLIENT_ID'],
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        # Extract token
        id_token = response['AuthenticationResult']['IdToken']
        access_token = response['AuthenticationResult']['AccessToken']
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'token': id_token,  # Use ID token for API Gateway Cognito authorizer
                'access_token': access_token,  # Keep access token for other uses
                'message': 'Login successful'
            })
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ['NotAuthorizedException', 'UserNotFoundException']:
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Invalid credentials'})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Authentication failed'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'LOGIN-FUNCTION: Internal server error'})
        }


def handle_forgot_password(event):
    """Handle forgot password request"""
    
    try:
        # Parse request body
        body = decode_payload(event.get('body', {}))
        username = body.get('username')
        
        if not username:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Username required'})
            }
        
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp')
        
        # Initiate forgot password flow
        cognito_client.forgot_password(
            ClientId=os.environ['CLIENT_ID'],
            Username=username
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Password reset code sent to your email'
            })
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UserNotFoundException':
            # For security, don't reveal if user exists or not
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'If the email exists, a reset code has been sent'
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to send reset code'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'FORGOT PASSWORD Internal server error'})
        }

def handle_reset_password(event):
    """Handle password reset confirmation"""
    
    try:
        # Parse request body
        body = decode_payload(event.get('body', {}))
        username = body.get('username')
        code = body.get('code')
        new_password = body.get('new_password')
        
        if not username or not code or not new_password:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Username, code, and new password required'})
            }
        
        # Initialize Cognito client
        cognito_client = boto3.client('cognito-idp')
        
        # Confirm forgot password
        cognito_client.confirm_forgot_password(
            ClientId=os.environ['CLIENT_ID'],
            Username=username,
            ConfirmationCode=code,
            Password=new_password
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Password reset successful'
            })
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'CodeMismatchException':
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid verification code'})
            }
        elif error_code == 'ExpiredCodeException':
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Verification code has expired'})
            }
        elif error_code == 'InvalidPasswordException':
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Password does not meet requirements'})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to reset password'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'RESET PASSWORD Internal server error'})
        }

def decode_payload(base64_str: str) -> dict:
    """
    Decode a Base64 string back to a JSON payload
    Args:
        base64_str (str): The Base64 string to decode
    Returns:
        dict: The decoded JSON payload
    """
    # Decode the Base64 string to bytes
    json_bytes = base64.b64decode(base64_str)

    # Decode the bytes to a JSON string
    json_str = json_bytes.decode('utf-8')

    # Parse the JSON string to a dictionary
    payload = json.loads(json_str)

    return payload