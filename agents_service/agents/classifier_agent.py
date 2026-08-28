import os
from collections.abc import AsyncIterable

from dotenv import load_dotenv
from pydantic_ai import Agent, ModelMessagesTypeAdapter
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

from agents_service.models import IntentClassification
from agents_service.prompts import (
    CLASSIFIER_AGENT_INSTRUCTIONS,
    CLASSIFIER_PROMPT_TEMPLATE,
)

load_dotenv()

model_name: str = os.getenv("INTENT_CLASSIFIER_MODEL", "qwen/qwen3.6-27b")


def get_classifier_agent() -> Agent:
    model = GroqModel(
        model_name,
        provider=GroqProvider(
            # base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("GROQ_API_KEY", ""),
        ),
    )
    classifier_agent = Agent(
        model,
        instructions=CLASSIFIER_AGENT_INSTRUCTIONS,
        output_type=IntentClassification,
    )
    return classifier_agent


async def classify_query(
    query: str,
    classifier_agent: Agent | None = None,
) -> IntentClassification:
    """
    Classifies the intent of a given query, and also provides a response for certain intents.

    Args:
        query (str): The input query to classify.

    Returns:
        IntentClassification: An object containing the classified intent and an optional response.
    """
    if classifier_agent is None:
        classifier_agent = get_classifier_agent()
    prompt = CLASSIFIER_PROMPT_TEMPLATE.format(query=query)
    classification = await classifier_agent.run(prompt)
    return classification.output


async def classify_query_stream(
    query: str,
    message_history: list[ModelMessage] | None = None,
    classifier_agent: Agent | None = None,
) -> AsyncIterable[str] | IntentClassification:
    if classifier_agent is None:
        classifier_agent = get_classifier_agent()
    prompt = CLASSIFIER_PROMPT_TEMPLATE.format(query=query)
    async with classifier_agent.run_stream(
        prompt, message_history=message_history
    ) as result:
        async for message in result.stream_output():
            yield message
