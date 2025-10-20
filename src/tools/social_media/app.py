import json
import asyncio
from social_media_tool import social_media_logic

def lambda_handler(event, context):
    print(f"Received event for ideation: {json.dumps(event)}")
    
    try:
        params = event.get('parameters', [])
        video_title_param = next((p for p in params if p['name'] == 'video_title'), None)
        core_angle_param = next((p for p in params if p['name'] == 'core_angle'), None)
        central_question_param = next((p for p in params if p['name'] == 'central_question'), None)
        supporting_research_param = next((p for p in params if p['name'] == 'supporting_research'), None)
        platform_param = next((p for p in params if p['name'] == 'platform'), None)
        
        if not all(
            [platform_param,
             video_title_param, 
             core_angle_param,
             central_question_param,
             supporting_research_param
             ]
             ):
            raise ValueError("Missing all or one of the required parameters")
            
        platform = platform_param['value']
        video_title = video_title_param['value']
        core_angle = core_angle_param['value']
        central_question = central_question_param['value']
        supporting_research = supporting_research_param['value']

        result = social_media_logic(
            platform=platform,
            video_title=video_title,
            core_angle=core_angle,
            central_question=central_question,
            supporting_research=supporting_research
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