# In src/api_handler/app.py
import json
import boto3
import os

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
AGENT_ID = os.environ.get("BEDROCK_AGENT_ID")
AGENT_ALIAS_ID = os.environ.get("BEDROCK_AGENT_ALIAS_ID") # Usually 'TSTALIASID' for the draft

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # The user's prompt comes from the Streamlit UI in the event body
        body = json.loads(event.get('body', '{}'))
        user_input = body.get('inputText')
        session_id = body.get('sessionId', 'default-session')

        if not user_input:
            return {'statusCode': 400, 'body': json.dumps({'error': 'inputText is required'})}

        # Invoke the Bedrock Agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=user_input
        )

        # The response from invoke_agent is a streaming body.
        # We need to read it and send it back.
        completion = ""
        for event_chunk in response['completion']:
            chunk = event_chunk['chunk']
            completion += chunk['bytes'].decode('utf-8')

        return {
            'statusCode': 200,
            'headers': { 'Content-Type': 'application/json' },
            'body': completion # Send back the final agent response
        }

    except Exception as e:
        print(f"ERROR: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}