import boto3
import json
from botocore.exceptions import ClientError
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))
from prompts.scriptwriting_prompt import SCRIPTWRITING_PROMPT
from strands import tool

client = boto3.client("bedrock-runtime", region_name="us-east-1")

@tool
def scriptwriting_tool(
        video_title:str,
        raw_research_content:str,
        core_angle:str,
        central_question:str
        ) -> dict:
    
    model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
    #model_id = "anthropic.claude-sonnet-4-20250514-v1:0"

    print("--Starting Script Generation--")

    prompt = SCRIPTWRITING_PROMPT.format(video_title=video_title,
                                         raw_research_content=raw_research_content,
                                         core_angle=core_angle,
                                         central_question=central_question
                                         )

    native_request = {
        "anthropic_version":"bedrock-2023-05-31",
        "max_tokens": 8192,
        "temperature": 0.85,
        "messages": [
            {
                "role":"user",
                "content":[{"type":"text","text":prompt}]
            }
        ]
    }
    request_body = json.dumps(native_request)

    try:
        response = client.invoke_model(
            modelId=model_id,
            body=request_body
        )

    except(ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        return {"error":str(e)}
    
    response_body = json.loads(response.get("body").read())
    response_text = response_body.get("content")[0].get("text")

    try:
        script_data = json.loads(response_text)
        if script_data:
            print("--Script generation successful.--")
            return script_data
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from model response. Reason: {e}")
        print(f"Model's raw response: {response_text}")
        return {"error": "Failed to parse model response."}
    

if __name__ == '__main__':

    video_title="""
    From Caribbean Beaches to Champions League Glory: How Dwight Yorke Silenced All Doubters
    """
    core_angle="""
The Misjudged Hero
"""
    central_question="""
How did a striker from tiny Trinidad and Tobago become Manchester United's unlikely savior in their most historic season?
"""
    sample_research = """
Dwight Yorke, from Trinidad and Tobago, joined Aston Villa in 1989 after being discovered on a pre-season tour. 
Despite early struggles with his finishing, he became a key player. 
He moved to Manchester United in 1998 for £12.6 million, a controversial transfer. 
At Man Utd, he formed a legendary partnership with Andy Cole, winning the Treble (Premier League, FA Cup, Champions League) in his very first season. 
Many doubted if a player from a small nation could lead the line for the biggest club in the world, but he scored 29 goals that season, finishing as the Premier League's top scorer.
"""

    
    generated_script = scriptwriting_tool(
        raw_research_content=sample_research,
        core_angle=core_angle,
        central_question=central_question,
        video_title=video_title                                      
                                          )
    
    if "error" not in generated_script:
        print("\n\n--- GENERATED SCRIPT ---")
        print("\n--- Script Body ---")
        print(generated_script.get('script_body'))




