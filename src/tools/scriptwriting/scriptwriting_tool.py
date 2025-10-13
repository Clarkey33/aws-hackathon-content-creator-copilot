import boto3
import json
from botocore.exceptions import ClientError
import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))
from prompts import scriptwriting_prompt

client = boto3.client("bedrock-runtime", region_name="us-east-1")

def scriptwriting_tool(
        video_title:str,
        research_content:str,
        core_angle:str,
        central_question:str
        ) -> dict:
    
    model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"

    print("--Starting Script Generation--")

    prompt = scriptwriting_prompt

    native_request = {
        "anthropic_version":"bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.7,
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
            body=request
        )

    except(ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        return {"error":str(e)}
    
    response_body = json.loads(response.get("body").read())
    response_text = response.get("content")[0].get("text")

    try:
        script_data = json.loads(response_text)
        if script_data:
            print("--Script generation successful.--")
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from model response. Reason: {e}")
        print(f"Model's raw response: {response_text}")
        return {"error": "Failed to parse model response."}
    

if __name__ == '__main__':

    sample_research = """
The 2022 FIFA World Cup was won by Argentina, who defeated France in the final. 
The match was a thriller, ending 3-3 after extra time and going to penalties, which Argentina won 4-2. 
Lionel Messi was the captain of the Argentinian team and was awarded the Golden Ball as the best player of the tournament, scoring 7 goals. 
Kylian Mbappé of France won the Golden Boot as the top goalscorer with 8 goals, including a hat-trick in the final.
"""
    
    generated_script = scriptwriting_tool(research_summary=sample_research)
    
    if "error" not in generated_script:
        print("\n\n--- GENERATED SCRIPT ---")
        print(f"Title: {generated_script.get('title')}")
        print("\n--- Script Body ---")
        print(generated_script.get('script_body'))




