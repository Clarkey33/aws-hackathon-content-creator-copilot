import json
import asyncio
from ideation_tool import ideation_logic

def lambda_handler(event, context):
    print(f"Received event for ideation: {json.dumps(event)}")
    
    try:
        params = event.get('parameters', [])
        research_param = next((p for p in params if p['name'] == 'research_summary'), None)
        
        if not research_param:
            raise ValueError("Missing required parameter: 'research_summary'")
            
        research_summary = research_param['value']

        result = ideation_logic(research_summary=research_summary) 
        
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