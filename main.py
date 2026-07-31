import asyncio

from agents_service.agents import create_research_plan
from agents_service.pipeline.executor import execute_research_phase
from custom_logger import get_logger

# logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = get_logger()


async def main():
    goal = "Prepare a report on applications of electrical heating, and explain 2 applications in detail"
    plan = await create_research_plan(goal, ["technology", "scientific_or_academic"])

    print(f"Plan has {len(plan.tasks)} tasks, executing research phase...\n")

    results = await execute_research_phase(plan, max_concurrency=2)

    for task_id, result in results.items():
        print(f"\n=== {task_id} ({result.status}) ===")
        print(result.summary)


if __name__ == "__main__":
    asyncio.run(main())
