import json
import asyncio
from scriptwriting_tool import scriptwriting_logic
import boto3
from urllib.parse import urlparse

s3_client = boto3.client("s3")

def lambda_handler(event, context):
    print(f"Received event for ideation: {json.dumps(event)}")
    
    try:
        params = event.get('parameters', [])
        video_title_param = next((p for p in params if p['name'] == 'video_title'), None)
        raw_content_uri_param = next((p for p in params if p['name'] == 'raw_content_uri'), None)
        core_angle_param = next((p for p in params if p['name'] == 'core_angle'), None)
        central_question_param = next((p for p in params if p['name'] == 'central_question'), None)
        
        if not all([video_title_param, raw_content_uri_param, core_angle_param, central_question_param]):
            raise ValueError(
                "Missing all or one of the required parameters: 'video_title','raw_content','core_angle', 'central_question'"
                )
            
        video_title = video_title_param['value']
        raw_content_uri = raw_content_uri_param['value']
        core_angle = core_angle_param['value']
        central_question = central_question_param['value']

        print(f"Fetching content from S3 URI: {raw_content_uri}")
        parsed_uri = urlparse(raw_content_uri, allow_fragments=False)
        bucket_name = parsed_uri.netloc
        object_key = parsed_uri.path.lstrip('/')
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        raw_research_content = s3_response['Body'].read().decode('utf-8')
        
        print("Successfully fetched and decoded content from S3.")

        result = scriptwriting_logic(
            core_angle=core_angle,
            raw_research_content=raw_research_content,
            video_title=video_title,
            central_question=central_question 
            ) 
        
        response = {
            'response': {
                'actionGroup': event['actionGroup'],
                'function': event['function'],
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {'body': json.dumps(result)}
                    }
                }
            },
            'sessionId': event['sessionId'],
            'sessionAttributes': event.get('sessionAttributes', {})
        }

        return response
    except Exception as e:
        print(f"ERROR: {e}")