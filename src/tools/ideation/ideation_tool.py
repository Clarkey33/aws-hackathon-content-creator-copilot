import boto3
import json
import os
from botocore.exceptions import ClientError

import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))
from prompts.ideation_prompt import IDEATION_PROMPT

# This client should be at the top of your tools.py file, initialized once.
bedrock_client = boto3.client(
    "bedrock-runtime", 
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

def ideation_tool(raw_research_content: str) -> dict:

    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    print("-- Starting ideation and angle finding... --")
    
    prompt = IDEATION_PROMPT.format(raw_research_content=raw_research_content)

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "temperature": 0.85, 
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }

    request_body = json.dumps(native_request)

    try:
        response = bedrock_client.invoke_model(modelId=model_id, body=request_body)
    except (ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        return {"error": str(e)}

    response_body = json.loads(response.get("body").read())
    response_text = response_body.get("content")[0].get("text")
    
    try:
        idea_data = json.loads(response_text)
        print("--- Stage: Ideation successful. ---")
        return idea_data
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from ideation model response. Reason: {e}")
        print(f"Model's raw response: {response_text}")
        return {"error": "Failed to parse model response."}


if __name__ == '__main__':
    sample_research = """
Dwight Yorke, from Trinidad and Tobago, joined Aston Villa in 1989 after being discovered on a pre-season tour. 
Despite early struggles with his finishing, he became a key player. 
He moved to Manchester United in 1998 for £12.6 million, a controversial transfer. 
At Man Utd, he formed a legendary partnership with Andy Cole, winning the Treble (Premier League, FA Cup, Champions League) in his very first season. 
Many doubted if a player from a small nation could lead the line for the biggest club in the world, but he scored 29 goals that season, finishing as the Premier League's top scorer.
"""
    
    video_idea = ideation_tool(raw_research_content=sample_research)
    
    if "error" not in video_idea:
        print("\n\n--- GENERATED VIDEO IDEA ---")
        print(f"Title: {video_idea.get('video_title')}")
        print(f"Core Angle: {video_idea.get('core_angle')}")
        print(f"Central Question: {video_idea.get('central_question')}")