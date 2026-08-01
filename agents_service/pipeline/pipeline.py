from agents_service.agents import classify_query, create_research_plan
from agents_service.models import IntentEnum, Report
from agents_service.pipeline.create_report import generate_report
from agents_service.pipeline.executor import execute_research_phase
from custom_logger import get_logger

logger = get_logger()


async def run_pipeline(query: str) -> str | Report:
    """
    Runs the full pipeline: classify -> decompose -> execute research -> synthesize.
    Returns either a plain string (for GREETING/UNSUPPORTED) or a Report (for RESEARCH_TOPIC).
    """
    classification = await classify_query(query)
    logger.info(
        f"Classified as {classification.intent} | categories={classification.categories}"
    )

    if classification.intent != IntentEnum.RESEARCH_TOPIC:
        return classification.response

    categories = [c.value for c in classification.categories]

    plan = await create_research_plan(query, categories)
    logger.info(f"Plan generated with {len(plan.tasks)} tasks")

    results = await execute_research_phase(plan, max_concurrency=1)
    succeeded = sum(1 for r in results.values() if r.status.value == "success")
    logger.info(f"Research phase complete: {succeeded}/{len(results)} tasks succeeded")

    report = await generate_report(query, results)
    logger.info(f"Report generated: '{report.title}' ({len(report.content)} chars)")

    return report
