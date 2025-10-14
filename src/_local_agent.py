import asyncio
from strands import Agent, tool
from strands_tools import handoff_to_user
from strands.models import BedrockModel
import sys
from pathlib import Path
import os

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from src.tools.ideation import ideation_tool
from src.tools.research import research_tool
from src.tools.scriptwriting import scriptwriting_tool
from src.tools.social_media import social_media_tool
from prompts.master_prompt import MASTER_PROMPT


bedrock_model = BedrockModel(
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
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


async def main():
    print("--Creator Copilot Engaged--")
    user_request="Create a full content package about the career of Dwight Yorke."

    creator_copilot(user_request)

    print("\n--Agent has completed task.--")
    
if __name__ == "__main__":
    asyncio.run(main())
