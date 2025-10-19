import sys
import json
import os
from pathlib import Path
from dotenv import load_dotenv

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

import boto3
import uuid
import asyncio
from tavily import AsyncTavilyClient
#from config import API_KEY_TAVILY,S3_BUCKET_NAME
from models import ResearchResult, InputQuery 
from strands import tool


_CACHED_SECRETS = {}

def get_secret(secret_name):
   
    if secret_name in _CACHED_SECRETS:
        return _CACHED_SECRETS[secret_name]

    param_name = os.getenv(f"{secret_name}_PARAM_NAME")
    if param_name:
        print(f"Fetching secret '{secret_name}' from Parameter Store...")
        ssm_client = boto3.client('ssm')
        response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
        secret_value = response['Parameter']['Value']
    else:
        print(f"Fetching secret '{secret_name}' from local environment variables...")
        secret_value = os.getenv(secret_name)

    if not secret_value:
        raise ValueError(f"Secret '{secret_name}' could not be found.")

    _CACHED_SECRETS[secret_name] = secret_value
    return secret_value


load_dotenv() 

s3_client = boto3.client("s3")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
tavily_client = None

if not S3_BUCKET_NAME:
        error_msg = "CRITICAL ERROR: S3_BUCKET_NAME is not configured. Please check your .env file or Lambda environment variables."
        print("error: ",error_msg)
        #return {"error": error_msg}
#global tavily_client
if tavily_client is None:
    api_key = get_secret("API_KEY_TAVILY")
    tavily_client = AsyncTavilyClient(api_key=api_key)



@tool
async def research_tool(queries: list[str]) -> list[dict]:

    print(f"--- Received queries for research_tool: {queries} ---")
    print(f"--- Type of queries variable: {type(queries)} ---")

    if not isinstance(queries, list) or not all(isinstance(q, str) for q in queries):
        raise ValueError("Error: input value must be a list of strings.")
    
    input_queries = [InputQuery(query=q) for q in queries]
    
    print("--- Stage 1: Starting concurrent searches... ---")
    search_tasks = [asyncio.create_task(tavily_client.search(**query.model_dump())) for query in input_queries]
    #print(f"\nSearch tasks: {search_tasks}")
    search_results_list = await asyncio.gather(*search_tasks)

    print("--- Stage 2: Finding relevant URLs... ---")
    #print(f"\nSearch Results list: {search_results_list}\n")
    url_to_query_map = []
    for i, result_dict in enumerate(search_results_list):
        original_query = input_queries[i].query
        for url_info in result_dict.get('results',[]):
            if url_info.get('score',0) > 0.81:
                url_to_query_map.append(
                    {'url':url_info.get('url'),
                     'query':original_query,
                     'research_summary':result_dict.get('answer','')
                     }
                     )       
    #print(f"\n URL to QUERY MAP: {url_to_query_map}\n")

    if not url_to_query_map:
        print("No highly relevant URLs found to extract.")
        return []
    
    all_urls = list(set(item['url'] for item in url_to_query_map))
    
    #print(f"Relevant urls: {relevant_urls}\n")
    print(f"\n--- Stage 3: Concurrently extracting content from {len(all_urls)} URLs... ---")
    
    extracted_data_list = await tavily_client.extract(urls=all_urls)

    content_lookup = {
        item.get('url', ''): item.get('raw_content', '')
        for item in extracted_data_list.get('results', [])
        }

    print("--- Stage 4: Aggregating content and structuring the output... ---")

    all_raw_content = []
    for mapping in url_to_query_map:
        content = content_lookup.get(mapping['url'])
        if content:
            all_raw_content.append(content)
            
    if not all_raw_content:
        return {"error": "Failed to extract content from any URLs."}
    
    combined_raw_content = "\n\n--- NEW SOURCE ---\n\n".join(all_raw_content)
    first_summary = search_results_list[0].get('answer', "No summary available.")

    print(f"\n--- Writing Combined Raw Content to S3 bucket---")
    file_key= f"research-output-{uuid.uuid4()}.txt"
    print(f"--- Attempting to save content to S3: s3://{S3_BUCKET_NAME}/{file_key} ---")

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=combined_raw_content.encode('utf-8') 
        )
        s3_uri = f"s3://{S3_BUCKET_NAME}/{file_key}"
        print(f"--- SUCCESS: Research content saved to {s3_uri} ---")
        
        final_result = ResearchResult(
            research_summary=first_summary,
            s3_uri=s3_uri
        )
        return final_result.model_dump()
    
    except Exception as e:
        print("--- ERROR: FAILED TO WRITE TO S3 ---")
        print(f"Bucket Name: {S3_BUCKET_NAME}")
        print(f"File Key: {file_key}")
        print(f"Error Type: {type(e).__name__}")
        print(f"Full Error Details: {e}")
        return {"error": f"Failed to save research to S3: {e}"}

    #return [result.model_dump() for result in final_results]


def lambda_handler(event, context):
    
    print(f"Received event from Bedrock Agent: {json.dumps(event)}")
    
    try:
        params = event.get('parameters', [])
        
        queries_param = next((p for p in params if p['name'] == 'queries'), None)
        
        if not queries_param:
            raise ValueError("Missing required parameter: 'queries'")
            
        queries = queries_param['value']

        result = asyncio.run(research_tool(queries=queries))
        
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
       



async def main():

    queries =[
        "Dwight Yorke's impact on Manchester United during their treble-winning season",
        "The evolution of Dwight Yorke's playing style throughout his career?"
    ]

    results = await research_tool(queries)
    #print('results', results)
    print("\n\n--- FINAL EXTRACTED CONTENT ---")
    
    if results:
        for result in results:
            print(f"\n--- Query: {result.get('query')} ---")
            print(f"\n--- Research summary: {result.get('research_summary')}")
            print(f"\nraw research content: {result.get('raw_content')}\n")
    else:
        print("No content was extracted.")

if __name__ == "__main__":
    asyncio.run(main())


