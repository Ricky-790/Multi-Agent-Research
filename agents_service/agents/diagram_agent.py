import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from agents_service.models.diagram_models import DiagramAgentOutput
from agents_service.models.sub_agent_models import DiagramData
from agents_service.prompts import (
    DIAGRAM_AGENT_PROMPT,
    DIAGRAM_AGENT_SYSTEM_INSTRUCTIONS,
)
from agents_service.prompts.diagram_prompts import build_data_block

load_dotenv()


def get_diagram_agent() -> Agent:
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
        output_type=DiagramAgentOutput,
        instructions=DIAGRAM_AGENT_SYSTEM_INSTRUCTIONS,
    )
    return code_gen_agent


async def generate_diagram_code(
    diagram_agent: Agent,
    diagram_data: DiagramData,
) -> DiagramAgentOutput:
    prompt = DIAGRAM_AGENT_PROMPT.format(
        diagram_type=diagram_data.diagram_type,
        caption=diagram_data.caption,
        data_block=build_data_block(diagram_data),
    )
    result = await diagram_agent.run(prompt)
    return result.output
