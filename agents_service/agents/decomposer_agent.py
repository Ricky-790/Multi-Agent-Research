import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider

from agents_service.models import ResearchPlan
from agents_service.prompts import (
    DECOMPOSER_PROMPT_TEMPLATE,
    build_decomposer_instructions,
)

load_dotenv()

model_name: str = os.getenv("DECOMPOSER_MODEL", "")


async def create_research_plan(goal: str, categories: list[str]) -> ResearchPlan:
    instructions = build_decomposer_instructions(categories)

    # model = GroqModel(
    #     model_name,
    #     provider=GroqProvider(api_key=os.getenv("GROQ_API_KEY", "")),
    # )
    model = GoogleModel(
        model_name,
        provider=GoogleProvider(api_key=os.getenv("GOOGLE_API_KEY", "")),
    )
    decomposer_agent = Agent(model, instructions=instructions, output_type=ResearchPlan)

    prompt = DECOMPOSER_PROMPT_TEMPLATE.format(
        goal=goal,
        categories=", ".join(categories),
    )

    result = await decomposer_agent.run(prompt)
    return result.output


import asyncio

from agents_service.agents import classify_query
from agents_service.models import IntentEnum


async def main():
    goal = "Prepare a report on applications of electrical heating, and explain 2 applications in detail"

    classification = await classify_query(goal)
    print(f"CLASSIFICATION:\n{classification}")

    if classification.intent.value == IntentEnum.RESEARCH_TOPIC:
        plan = await create_research_plan(
            goal, [c.value for c in classification.categories]
        )
        print(f"PLAN:\n{plan.model_dump_json(indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
