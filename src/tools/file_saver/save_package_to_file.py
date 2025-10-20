import boto3
import os
import uuid
import json
#from strands import tool
import sys
from pathlib import Path
#from dotenv import load_dotenv

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

#load_dotenv()
s3_client = boto3.client("s3")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

#@tool
def save_package_to_file_logic(
    video_title: str,
    script_body: str,
    twitter_post: str,
) -> dict:
   
    print("--- Finalizing and saving the complete content package... ---")
    
    # --- 1. Format the content into a single string ---
    final_content = f"""

## VIDEO TITLE
{video_title}


## FULL VIDEO SCRIPT
{script_body}


## TWITTER THREAD
{twitter_post}

"""

    file_key = f"final-content-package-{uuid.uuid4()}.txt"
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            Body=final_content.encode('utf-8')
        )
        print(f"--- Successfully saved package to s3://{S3_BUCKET_NAME}/{file_key} ---")

        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': file_key},
            ExpiresIn=3600
        )
        print(f"--- Generated download link: {download_url} ---")
        
        return {
            "status": "Success",
            "download_url": download_url
        }

    except Exception as e:
        print(f"ERROR: Could not save final package to S3. Reason: {e}")
        return {"error": f"Failed to save final package: {str(e)}"}


