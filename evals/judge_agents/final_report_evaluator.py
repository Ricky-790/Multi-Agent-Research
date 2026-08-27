import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from evals.judge_agents.score_models import ReportQualityScore
from evals.prompts import REPORT_EVAL_INSTRUCTIONS

load_dotenv()

model_name = os.getenv("EVALUATOR_MODEL", "deepseek-ai/deepseek-v4-flash-0731")

provider = OpenAIProvider(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY", ""),
)
model = OpenAIChatModel(model_name=model_name, provider=provider)

evaluator = Agent(
    model=model,
    output_type=ReportQualityScore,
    instructions=REPORT_EVAL_INSTRUCTIONS,
)
