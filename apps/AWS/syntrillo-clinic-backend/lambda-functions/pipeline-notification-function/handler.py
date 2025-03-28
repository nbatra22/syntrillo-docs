import json
import boto3
import os
from datetime import datetime

def handler(event, context):
    """
    Lambda function that processes CodePipeline notification events and sends formatted emails via SNS.
    
    The function:
    1. Parses the pipeline notification event
    2. Formats the notification into a readable message
    3. Sends the message using Amazon SNS
    
    Args:
        event (dict): The event data from the notification rule
        context (object): Lambda context object
    
    Returns:
        dict: Response indicating success or failure
    """
    print("Received event:", event)
    
    # try:
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')

    # Format the message more readably
    message_data = json.loads(event["Records"][0]["Sns"]["Message"])

    # Format timestamp to be more readable
    timestamp = datetime.fromisoformat(message_data["time"].replace('Z', '+00:00'))
    formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")

    formatted_message = f"""
Pipeline Notification
--------------------
Pipeline Name: {message_data["detail"]["pipeline"]}
Stage: {message_data["detail"]["stage"]}
State: {message_data["detail"]["state"]}
Time: {formatted_time}

Execution Details:
- Execution ID: {message_data["detail"]["execution-id"]}
- Pipeline Version: {message_data["detail"]["version"]}
- Attempt: {message_data["detail"]["pipeline-execution-attempt"]}
- Region: {message_data["region"]}
- Account: {message_data["account"]}

Pipeline ARN: {message_data["resources"][0]}
        """
        
    # Send the formatted message via SNS
    send_sns_notification(
        os.environ.get('SNS_TOPIC_ARN'),
        f"Pipeline {message_data['detail']['pipeline']} - Stage {message_data['detail']['stage']} - {message_data['detail']['state']}",
        formatted_message
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('SNS notification sent successfully')
    }
        
    # except Exception as e:
    #     print(f"Error processing notification: {str(e)}")

    #     return {
    #         'statusCode': 500,
    #         'body': json.dumps(f'Error processing notification: {str(e)}')
    #     }

def send_sns_notification(topic_arn, subject, message):
    """
    Send a notification using Amazon SNS
    
    Args:
        topic_arn (str): The ARN of the SNS topic
        subject (str): Email subject
        message (str): HTML formatted message body
    """
    sns_client = boto3.client('sns')
    
    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message,
        )
        print(f"SNS notification sent! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Error sending SNS notification: {str(e)}")
        raise e
