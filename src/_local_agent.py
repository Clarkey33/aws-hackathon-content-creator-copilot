import asyncio
from strands import Agent,tool
from strands_tools import handoff_to_user
from strands.models import BedrockModel
import sys
from pathlib import Path
import os
import glob

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from src.tools.ideation.ideation_tool import ideation_logic
from src.tools.research.research_tool import research_logic
from src.tools.scriptwriting.scriptwriting_tool import scriptwriting_logic
from src.tools.social_media.social_media_tool import social_media_logic
from src.tools.file_saver.save_package_to_file import save_package_to_file_logic
from prompts.master_prompt import MASTER_PROMPT

bedrock_model = BedrockModel(
    #model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    #model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
    #model_id="us.anthropic.claude-opus-4-20250514-v1:0",
    model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    region_name = "us-east-1",
    temperature = 0.7
    )

research_tool_local = tool(research_logic)
ideation_tool_local = tool(ideation_logic)
social_media_tool_local = tool(social_media_logic)
scriptwriting_tool_local = tool(scriptwriting_logic)
save_package_to_file_tool_local = tool(save_package_to_file_logic)

creator_copilot = Agent(model=bedrock_model,
                        system_prompt = MASTER_PROMPT,
                        tools=[
                            ideation_logic,
                            research_logic,
                            scriptwriting_logic,
                            social_media_logic,
                            save_package_to_file_logic,
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

        #creator_copilot(user_request)

        final_assets = {}
        agent_stream = creator_copilot.stream_async(user_request)

        async for event in agent_stream:
            event_type = event.get("type")
       
            if event_type == 'tool_output' and 'error' not in event.get("output",{}):
                tool_name = event.get("name")
                if tool_name:
                    print(f"--- CAPTURING ASSET from {tool_name} ---")
                    final_assets[tool_name] = event.get("output")
            elif event_type == 'finish':
                print("\n\n--- Agent's Final Summary ---")
                print(event.get("text","Agent finished without a summary."))

                print("\n\n--- Captured Final Assets ---")
                if final_assets.get('scriptwriting_tool'):
                    print("\n--- SCRIPT ---")
                    script_dict = final_assets.get('scriptwriting_tool')
                    print(script_dict.get('script_body', 'Script body not found.'))
                
                if final_assets.get('social_media_tool'):
                    print("\n--- SOCIAL MEDIA POST ---")
                    print(final_assets.get('social_media_tool'))

    except KeyboardInterrupt:
        print("\n\n-- Shutdown signal received. Exiting gracefully. --")
        cleanup_temp_files()
        
    except Exception as e:
        print(f"\n\n-- An unexpected error occurred: {e} --")
        cleanup_temp_files()

    finally:
        print("\n-- Agent has completed task. --")

    
if __name__ == "__main__":
    asyncio.run(main())
