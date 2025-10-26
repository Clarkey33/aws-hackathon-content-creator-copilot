import boto3
import json
import os
from botocore.exceptions import ClientError
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent 
sys.path.append(str(project_root))

from botocore.config import Config
from utils.json_parser import robust_json_parser
from prompts.social_media_prompt import SOCIAL_MEDIA_PROMPT
#from strands import tool

config = Config(read_timeout=1000)

bedrock_client = boto3.client(
    service_name="bedrock-runtime", 
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    config=config
)

#@tool
def social_media_logic(
    video_title: str,
    core_angle: str,
    central_question: str,
    platform: str,
    supporting_research:str
    ) -> dict:

    model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    #model_id = "anthropic.claude-3-7-sonnet-20250219-v1:0"
    

    if not all([video_title,central_question, core_angle, platform]):#supporting_research,platform]):
        print("Missing one or all inputs")

    print(f"central_question:{central_question}\ncore angle:{core_angle}\nvideo title:{video_title}\nplatform: {platform}\nsupporting research:{supporting_research}\n")
    print(f"-- Starting Social Media Post Creation.. --\n")

    prompt = SOCIAL_MEDIA_PROMPT.format(platform=platform,
                                        video_title=video_title,
                                        central_question=central_question,
                                        core_angle=core_angle,
                                        supporting_research=supporting_research)
 
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
    print("no issue 2")
    request_body = json.dumps(native_request)
    print("-- Attempting to retrieve the generated text --")
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


if __name__ == '__main__':

    platform= "twitter"
    video_title="""From Caribbean Beaches to Champions League Glory: How Dwight Yorke Silenced All Doubters"""
    core_angle="""The Misjudged Hero"""
    central_question="""How did a striker from tiny Trinidad and Tobago become Manchester United's unlikely savior in their most historic season?"""
    
    supporting_research = """
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

    
    social_media_post = social_media_logic(platform=platform, 
                                          video_title=video_title,
                                          central_question=central_question,
                                          core_angle= core_angle,
                                          supporting_research=supporting_research
                                          )
    
    if "error" not in social_media_post:
        print("\n\n--- GENERATED Social Media Post ---")
        print(f"'social_media_post': {social_media_post.get('social_media_post')}")
       