import asyncio
from strands import Agent, tool
from strands_tools import handoff_to_user
from strands.models import BedrockModel
import sys
from pathlib import Path
import os
import glob

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from src.tools.ideation import ideation_tool
from src.tools.research import research_tool
from src.tools.scriptwriting import scriptwriting_tool
from src.tools.social_media import social_media_tool
from prompts.master_prompt import MASTER_PROMPT


bedrock_model = BedrockModel(
    #model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name = "us-east-1",
    temperature = 0.7
    )

creator_copilot = Agent(model=bedrock_model,
                        system_prompt = MASTER_PROMPT,
                        tools=[
                            ideation_tool,
                            research_tool,
                            scriptwriting_tool,
                            social_media_tool,
                            handoff_to_user
                            ]
                        )

def cleanup_temp_files():
    """Removes any temporary files created during the workflow."""
    print("\n--- Cleaning up temporary research files... ---")
    files = glob.glob("temp_research/*.txt")
    if not files:
        print("No temporary files to clean.")
        return
        
    for f in files:
        try:
            os.remove(f)
            print(f"Removed: {f}")
        except OSError as e:
            print(f"Error removing file {f}: {e}")


async def main():
    print("--Creator Copilot Engaged--")
    try:
        user_request="Create a full content package about the career of Dwight Yorke."

        creator_copilot(user_request)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutdown signal received. Exiting gracefully.")
        cleanup_temp_files()
        
    except Exception as e:
        print(f"\n\n💥 An unexpected error occurred: {e}")
        cleanup_temp_files()

    finally:
        print("\n--Agent has completed task.--")

    
if __name__ == "__main__":
    asyncio.run(main())
