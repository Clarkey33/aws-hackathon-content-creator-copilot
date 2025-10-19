import boto3
import json
import os
from botocore.exceptions import ClientError

import sys
from pathlib import Path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))
from .prompts.ideation_prompt import IDEATION_PROMPT
from src.utils.json_parser import robust_json_parser
from strands import tool


bedrock_client = boto3.client(
    "bedrock-runtime", 
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

@tool
def ideation_tool(research_summary: str) -> dict:

    model_id="us.anthropic.claude-opus-4-20250514-v1:0"

    print("-- Starting ideation and angle finding... --")
    
    prompt = IDEATION_PROMPT.format(research_summary=research_summary)

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 8192,
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
        #idea_data = json.loads(response_text)
        idea_data = robust_json_parser(response_text)
        print("--- Stage: Ideation successful. ---")
        return idea_data
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from ideation model response. Reason: {e}")
        print(f"Model's raw response: {response_text}")
        return {"error": "Failed to parse model response."}
    
def lambda_handler(event, context):
    print(f"Received event for ideation: {json.dumps(event)}")
    
    try:
        params = event.get('parameters', [])
        research_param = next((p for p in params if p['name'] == 'research_summary'), None)
        
        if not research_param:
            raise ValueError("Missing required parameter: 'research_summary'")
            
        research_summary = research_param['value']

        result = ideation_tool(research_summary=research_summary) 
        
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


if __name__ == '__main__':
    research_summary = """
Dwight Yorke's playing style underwent significant evolution throughout his career, 
demonstrating remarkable adaptability across different positions and phases of his development. 
He began his professional career at Aston Villa in 1989 as a right winger, utilizing his pace and natural athleticism on the flanks. 
During the 1995-96 season, Yorke transitioned to a centre forward position where his fluid movement and natural scoring ability flourished,
 establishing him as one of the Premier League's top strikers and earning him the nickname "The Smiling Assassin" for his joyful demeanor even under physical pressure from opponents. His peak years came at Manchester United from 1998-2002, 
 where he formed a legendary partnership with Andy Cole and became a clinical finisher, scoring 48 goals in 96 league appearances while contributing crucial goals in Champions League matches against elite European clubs like Bayern Munich, Barcelona, and Juventus. As he aged, Yorke demonstrated exceptional tactical intelligence by reinventing himself once again, transitioning to a holding midfielder role at Sunderland at age 35, playing as a defensive midfielder in front of the back line rather than as an attacking threat, which allowed him to extend his career at the highest level by utilizing his experience and football intelligence rather than relying on pace and physical attributes.

 Dwight Yorke had a transformative impact on Manchester United during their historic 1998/99 treble-winning season, 
 serving as the catalyst that propelled the club to unprecedented success. Signed from Aston Villa at the start of that campaign,
Yorke finished as the Premier League's top scorer with 18 goals, sharing the Golden Boot with Jimmy Floyd Hasselbaink and Michael Owen, while forming a legendary striking partnership with Andy Cole that became the foundation of United's attack. His contributions extended far beyond domestic competition, as he scored crucial goals against European giants including Bayern Munich, Barcelona, Inter Milan, and Juventus in the Champions League, netting 8 goals total in the competition, and added 3 more in the FA Cup to help secure all three trophies. Yorke's 18 league goals were particularly decisive, with a third of them directly earning United 11 points that proved essential to their title triumph - without these crucial strikes, the team would have finished fourth rather than champions. His impact was so significant that he was awarded the Premier League Player of the Season, and his infectious smile and positive attitude helped maintain team morale during the intense pressure of competing on three fronts simultaneously, making him an indispensable figure in what Sir Alex Ferguson later described as his greatest achievement.

 """
    
    video_idea = ideation_tool(research_summary=research_summary)
    
    if "error" not in video_idea:
        print("\n\n--- GENERATED VIDEO IDEA ---")
        print(f"Title: {video_idea.get('video_title')}")
        print(f"Core Angle: {video_idea.get('core_angle')}")
        print(f"Central Question: {video_idea.get('central_question')}")