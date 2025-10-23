# In src/api_handler/app.py
import json
import boto3
import os
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
AGENT_ID = os.environ.get("BEDROCK_AGENT_ID")
AGENT_ALIAS_ID = os.environ.get("BEDROCK_AGENT_ALIAS_ID")
# --- DEFINE THE CORS HEADERS ONCE ---
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'OPTIONS,POST'
}
def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps('CORS check successful')
        }
    try:
        body = json.loads(event.get('body', '{}'))
        user_input = body.get('inputText')
        session_id = body.get('sessionId', 'default-session')
        if not user_input:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS, 
                'body': json.dumps({'error': 'inputText is required'})
            }
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=user_input
        )
        completion = ""
        for event_chunk in response['completion']:
            chunk = event_chunk['chunk']
            completion += chunk['bytes'].decode('utf-8')
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS, 
            'body': completion 
        }
    except Exception as e:
        print(f"ERROR: {e}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS, 
            'body': json.dumps({'error': str(e)})
        }
