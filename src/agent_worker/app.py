import json
import boto3
from botocore.config import Config
import os


config = Config(read_timeout=880)
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', config=config)

def lambda_handler(event, context):
    try:
        print(f"Worker started with event: {json.dumps(event)}")
        
       
        user_input = event['inputText']
        session_id = event['sessionId']
        
        
        agent_id = os.environ.get("BEDROCK_AGENT_ID")
        agent_alias_id = os.environ.get("BEDROCK_AGENT_ALIAS_ID")

        
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=user_input
        )
        
        completion = ""
        for event_chunk in response['completion']:
            chunk = event_chunk['chunk']
            if 'bytes' in chunk:
                completion += chunk['bytes'].decode('utf-8')
        
        print(f"Agent finished with completion: {completion}")
        

    except Exception as e:
        print(f"FATAL ERROR in agent_worker: {e}")
        