from agents_service.agents.synthesizer_agent import generate_outline, write_section
from agents_service.models import Report, ReportOutline, TaskResult
from agents_service.pipeline.rate_limiting import run_with_retry
from custom_logger import get_logger

logger = get_logger()


async def generate_report(goal: str, results: dict[str, TaskResult]) -> Report:
    outline: ReportOutline = await run_with_retry(generate_outline, goal, results)
    logger.info(f"Outline generated with {len(outline.sections)} sections")

    written_sections = []
    for section in sorted(outline.sections, key=lambda s: s.order):
        logger.info(f"Writing section {section.order}: {section.title}")
        content = await run_with_retry(write_section, goal, outline, section, results)
        written_sections.append(f"## {section.title}\n\n{content}")

    full_content = f"# {outline.title}\n\n" + "\n\n".join(written_sections)
    return Report(title=outline.title, content=full_content)
