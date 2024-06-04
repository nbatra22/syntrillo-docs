from Questionnaire import XLSXQuestionnaire

import boto3
s3 = boto3.resource('s3')

def handler(event, context):
    # print event to see it in cloudwatch in case we need to debug
    print(event)
    
    # Get the object from the S3 event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    
    # Download the file
    s3.Bucket(bucket_name).download_file(object_key, '/tmp/onboarding_nurse.xlsx')
    
    # Convert object into an healthie form
    xlsx_questionnaire = XLSXQuestionnaire("/tmp/onboarding_nurse.xlsx")
    json_questionnaire = xlsx_questionnaire.to_json_questionnaire()
    healthie_form = json_questionnaire.to_healthie_form()

    # Push the form to healthie platform
    healthie_form.push_to_healthie_platform()