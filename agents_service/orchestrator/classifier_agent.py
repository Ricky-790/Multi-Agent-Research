import os
from enum import Enum
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from agents_service.orchestrator.llm_instructions import (
    CLASSIFIER_AGENT_INSTRUCTIONS,
    CLASSIFIER_PROMPT_TEMPLATE,
)

load_dotenv()


class IntentEnum(str, Enum):
    GREETING = "greeting"  # "hi", "hello", "hey there"
    # SIMPLE_QUESTION = "simple_question"  # answerable directly
    RESEARCH_TOPIC = "research_topic"  # needs the full pipeline
    UNSUPPORTED = "unsupported"  # irrelevant or out of scope


class IntentClassification(BaseModel):
    intent: IntentEnum
    response: Optional[str] = Field(
        default=None,
        description="A ready-to-send response, ONLY populated for GREETING, SIMPLE_QUESTION, "
        "or UNSUPPORTED intents. Null for RESEARCH_TOPIC, since that goes through the pipeline.",
    )


model_name: str = os.getenv("INTENT_CLASSIFIER_MODEL", "google/gemma-4-26b-a4b-it:free")

model = OpenRouterModel(
    model_name,
    provider=OpenRouterProvider(),
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


if __name__ == "__main__":
    import asyncio

    async def main():
        print(await classify_query("Hello"))
        print(await classify_query("Whats lionel messi's full name"))
        print(
            await classify_query(
                "Please prepare a report on compaction vs summarization for ai agents"
            )
        )

    asyncio.run(main())
