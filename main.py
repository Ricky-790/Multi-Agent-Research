import asyncio

from agents_service.models import Report
from agents_service.pipeline import run_pipeline


async def main():
    result = await run_pipeline(
        "Please prepare a report on Eth vs Sol. Focus on both their price history, current market(both financial and technical), future prospects, etc."
    )
    with open("test.md", "w") as f:
        if isinstance(result, Report):
            f.write(result.title)
            f.write("\n")
            f.write(result.content)


if __name__ == "__main__":
    asyncio.run(main())
