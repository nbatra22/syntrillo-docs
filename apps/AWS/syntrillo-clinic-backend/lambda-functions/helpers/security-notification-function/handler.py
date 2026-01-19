import boto3
import json
import os

def handler(event, context):
    sns = boto3.client('sns')
    
    security_message = event['Records'][0]['Sns']['Message']
    security_message = json.loads(security_message)
    
    source = security_message["source"]    
    formatted_security_message = json.dumps(security_message, indent=2)
    
    subject = "UNKNOWN SOURCE SECURITY FINDING"
    
    if source == "aws.guardduty":
        subject = "GuardDuty Security Finding"
        
    if source == "aws.inspector2":
        severity = security_message.get("detail", {}).get("severity", "UNKNOWN")
        resources = security_message.get("detail", {}).get("resources", [])
        resource_type = resources[0].get("type", "UNKNOWN") if resources else "UNKNOWN"
        subject = f"InspectorV2 Security Finding - {severity} - {resource_type}"
    
    sns.publish(
        TopicArn=os.environ['SNS_TOPIC_ARN'],
        Subject=subject,
        Message=formatted_security_message
    )