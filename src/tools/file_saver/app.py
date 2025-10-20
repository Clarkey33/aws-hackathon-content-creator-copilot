import json
import asyncio
from save_package_to_file import save_package_to_file_logic 

def lambda_handler(event, context):
    print(f"Received events for saving: {json.dumps(event)}")
    
    try:
        params = event.get('parameters', [])
        video_title_param = next((p for p in params if p['name'] == 'video_title'), None)
        script_body_param = next((p for p in params if p['name'] == 'script_body'), None)
        twitter_post_param = next((p for p in params if p['name'] == 'twitter_post'), None)
        #linkedin_post_param = next((p for p in params if p['name'] == 'linkedin_post'), None)
        
        if not all([video_title_param, script_body_param, twitter_post_param]):
            raise ValueError(
                "Missing all or one of the required parameters: 'video_title', 'script_body', 'twitter_post'"
                )
            
        video_title = video_title_param['value']
        script_body = script_body_param['value']
        twitter_post = twitter_post_param['value']
        #linkedin_post = linkedin_post_param.get('value',"")

        result = save_package_to_file_logic(
                video_title=video_title,
                script_body=script_body,
                twitter_post=twitter_post,
                #linkedin_post=linkedin_post
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