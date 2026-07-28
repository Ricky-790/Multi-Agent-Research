import os
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from dotenv import load_dotenv
from agents_service.prompts import (
    build_decomposer_instructions,
    DECOMPOSER_PROMPT_TEMPLATE,
)
from agents_service.models import ResearchPlan

load_dotenv()

model_name: str = os.getenv("ORCHESTRATOR_MODEL")


async def create_research_plan(goal: str, categories: list[str]) -> ResearchPlan:
    instructions = build_decomposer_instructions(categories)

    model = GoogleModel(
        model_name,
        provider=GoogleProvider(api_key=os.getenv("GOOGLE_API_KEY", "")),
    )
    orchestrator = Agent(model, instructions=instructions, output_type=ResearchPlan)

    prompt = DECOMPOSER_PROMPT_TEMPLATE.format(
        goal=goal,
        categories=", ".join(categories),
    )

    result = await orchestrator.run(prompt)
    return result.output


import asyncio
from agents_service.agents import classify_query
from agents_service.models import IntentEnum


async def main():
    goal = "Prepare a report on applications of electrical heating, and explain 2 applications in detail"

    classification = await classify_query(goal)
    print(classification)

    if classification.intent.value == IntentEnum.RESEARCH_TOPIC:
        plan = await create_research_plan(
            goal, [c.value for c in classification.categories]
        )
        print(plan.model_dump_json(indent=2))


asyncio.run(main())
