import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

from agents_service.models import IntentClassification
from agents_service.prompts import (
    CLASSIFIER_AGENT_INSTRUCTIONS,
    CLASSIFIER_PROMPT_TEMPLATE,
)

load_dotenv()

model_name: str = os.getenv("INTENT_CLASSIFIER_MODEL", "google/gemma-4-26b-a4b-it:free")

model = GroqModel(
    model_name,
    provider=GroqProvider(api_key=os.getenv("GROQ_API_KEY", "")),
)
classifier_agent = Agent(
    model, instructions=CLASSIFIER_AGENT_INSTRUCTIONS, output_type=IntentClassification
)


async def classify_query(query: str) -> IntentClassification:
    """
    Classifies the intent of a given query, and also provides a response for certain intents.

    Args:
        query (str): The input query to classify.

    Returns:
        IntentClassification: An object containing the classified intent and an optional response.
    """
    prompt = CLASSIFIER_PROMPT_TEMPLATE.format(query=query)
    classification = await classifier_agent.run(prompt)
    return classification.output


# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         print(await classify_query("NVIDIA"))
#     asyncio.run(main())
