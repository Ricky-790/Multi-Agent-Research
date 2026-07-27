import os
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from dotenv import load_dotenv

load_dotenv()

model_name: str = os.getenv("INTENT_CLASSIFIER_MODEL", "google/gemma-4-26b-a4b-it:free")

model = OpenRouterModel(
    model_name,
    provider=OpenRouterProvider(),
)
classifier_agent = Agent(model, instructions="")
