import boto3
import json
from botocore.exceptions import ClientError
import os
#from urllib.parse import urlparse
from prompts.scriptwriting_prompt import SCRIPTWRITING_PROMPT
from botocore.config import Config
#from strands import tool
#from src.utils.json_parser import robust_json_parser

config = Config(read_timeout=1000, connect_timeout=120,retries={'max_attempts':5})

client = boto3.client(
    "bedrock-runtime", 
    region_name= "us-east-1" #os.getenv("AWS_REGION", "us-east-1" ),
    config=config
)

#s3_client = boto3.client("s3")

def extract_script_from_raw_response(raw_response: str) -> dict:
   
    try:
        
        start_index = raw_response.find('{')
        end_index = raw_response.rfind('}')
        
        if start_index == -1 or end_index == -1:
            print("ERROR: Could not find a complete JSON object structure ({...}) in the response.")
            raise ValueError("Incomplete JSON object in response.")
            
        json_string = raw_response[start_index : end_index + 1]
        
        start_marker = '"script_body": "'
        end_marker = '"' 
        
        content_start_index = json_string.find(start_marker)
        if content_start_index == -1:
            print("ERROR: Could not find 'script_body' key in the JSON part of the response.")
            raise ValueError("Missing 'script_body' key.")
        
        content_start_index += len(start_marker)
        
        content_end_index = json_string.rfind(end_marker, content_start_index)
        
        if content_end_index == -1:
            print("ERROR: Could not find the closing quote for the 'script_body' value.")
            raise ValueError("Unterminated 'script_body' string.")
            
        script_content = json_string[content_start_index:content_end_index]

        script_content = script_content.replace('\\n', '\n').replace('\\"', '"')
        
        print("-- Successfully extracted script content using robust method. --")
        return {"script_body": script_content}

    except Exception as e:
        print(f"ERROR: Robust extraction failed. Reason: {e}")
        print(f"Model's raw response that failed extraction: {raw_response}")
        return {"error": "Failed to parse or extract script from the model's response."}


#@tool
def scriptwriting_logic(
        video_title:str,
        raw_research_content:str,
        core_angle:str,
        central_question:str
        ) -> dict:
    

    print("--Creating concise briefing document from full research--")
    try:
        summarization_prompt = f"""
You are a research analyst. Read the following extensive research document and create a concise,
fact-rich summary (around 500-600 words) that captures all the essential information needed to 
write a video script about "{video_title}". 
Focus on the core narrative, key statistics, defining moments, and direct quotes if available.

<research_document>
{raw_research_content}
</research_document>

Output only the summary text and nothing else.
"""
        
        summarizer_model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        #summarizer_model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
        
        summarizer_request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096, 
            "temperature": 0.4, 
            "messages": [{"role": "user", "content": [{"type": "text", "text": summarization_prompt}]}]
        }
        summarizer_body = json.dumps(summarizer_request)

        response = client.invoke_model(
                                       modelId=summarizer_model_id,
                                       body=summarizer_body
                                                            )
        response_body = json.loads(response.get("body").read())
        briefing_document = response_body.get("content")[0].get("text")
        print("--Briefing document created successfully.--")

    except (ClientError, Exception) as e:
        print(f"ERROR: Failed to create briefing document. Reason: {e}")
        return {"error": f"Failed to summarize research: {str(e)}"}


   
    #model_id="us.anthropic.claude-sonnet-4-20250514-v1:0"
    model_id="us.anthropic.claude-3-5-sonnet-20240620-v1:0"
    #model_id = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    #model_id = "anthropic.claude-haiku-4-5-20251001-v1:0"
    
    print("--Starting Script Generation (streaming mode)--")

    prompt = SCRIPTWRITING_PROMPT.format(video_title=video_title,
                                         raw_research_content=briefing_document,
                                         core_angle=core_angle,
                                         central_question=central_question
                                         )

    native_request = {
        "anthropic_version":"bedrock-2023-05-31",
        "max_tokens": 4096,
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
        response_text = ""
        with client.invoke_model_with_response_stream(
            modelId=model_id,
            body=request_body
        ) as stream:
            for event in stream["body"]:
                chunk = event.get("chunk")
                if chunk:
                    response_text += chunk["bytes"].decode("utf-8")
        print("--Streaming complete. Parsing output.--")

    except(ClientError, Exception) as e:
        print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
        return {"error":str(e)}
    
    response_body = json.loads(response.get("body").read())
    response_text = response_body.get("content")[0].get("text")

    script_data = extract_script_from_raw_response(response_text)
    #script_data = robust_json_parser(response_text)

    if "error" not in script_data:
        print("--Script generation successful.--")

    return script_data

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

    
    generated_script = scriptwriting_logic(
        raw_research_content=sample_research,
        core_angle=core_angle,
        central_question=central_question,
        video_title=video_title                                      
                                          )
    
    if "error" not in generated_script:
        print("\n\n--- GENERATED SCRIPT ---")
        print("\n--- Script Body ---")
        print(generated_script.get('script_body'))




