import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from agents_service.prompts import (
    DIAGRAM_AGENT_PROMPT,
    DIAGRAM_AGENT_SYSTEM_INSTRUCTIONS,
)

load_dotenv()


def get_diagram_agent()-> Agent:
    model_name = os.getenv("CODE_GENERATION_MODEL", "minimaxai/minimax-m3")
    code_gen_model = OpenAIChatModel(
        model_name,
        provider=OpenAIProvider(
            base_url="https://integrate.api.nvidia.com/v1/chat",
            api_key=os.getenv("NVIDIA_API_KEY", ""),
        ),
    )
    code_gen_agent = Agent(
        code_gen_model,
        output_type=str,
        instructions=DIAGRAM_AGENT_SYSTEM_INSTRUCTIONS,
    )
    return code_gen_agent
