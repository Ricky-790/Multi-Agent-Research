import os

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from agents_service.models import (
    Report,
    ReportOutline,
    ReportSection,
    Task,
    TaskResult,
    TaskResultStatus,
)
from agents_service.prompts import (
    OUTLINE_AGENT_INSTRUCTIONS,
    OUTLINE_PROMPT_TEMPLATE,
    SECTION_WRITER_INSTRUCTIONS,
    SECTION_WRITER_PROMPT_TEMPLATE,
)

outline_model_name = os.getenv("OUTLINE_MODEL", "gemini-3.1-flash-lite")
section_model_name = os.getenv("SECTION_WRITER_MODEL", "gemini-3.1-flash-lite")


def get_outline_agent():
    outline_model = GoogleModel(
        outline_model_name,
        provider=GoogleProvider(api_key=os.getenv("GOOGLE_API_KEY", "")),
    )
    outline_agent = Agent(
        outline_model,
        output_type=ReportOutline,
        instructions=OUTLINE_AGENT_INSTRUCTIONS,
    )
    return outline_agent


def get_section_writer_agent():
    section_model = GoogleModel(
        section_model_name,
        provider=GoogleProvider(api_key=os.getenv("GOOGLE_API_KEY", "")),
    )
    section_writer_agent = Agent(
        section_model,
        output_type=str,
        instructions=SECTION_WRITER_INSTRUCTIONS,
    )
    return section_writer_agent


def _build_summaries_block(results: dict[str, TaskResult]) -> str:
    blocks = []
    for task_id, result in results.items():
        if result.status == TaskResultStatus.FAILED:
            continue
        blocks.append(f"[{task_id}] {result.summary}")
    return "\n\n".join(blocks)


def _build_findings_block(task_ids: list[str], results: dict[str, TaskResult]) -> str:
    if not task_ids:
        return "(no specific findings — synthesize from the goal and overall outline instead)"

    blocks = []
    for task_id in task_ids:
        result = results.get(task_id)
        if result is None or result.status == TaskResultStatus.FAILED:
            continue
        findings_list = "\n".join(
            f"- {f.point}"
            + (f" ({f.supporting_detail})" if f.supporting_detail else "")
            for f in result.key_findings
        )
        blocks.append(f"From [{task_id}] — {result.summary}\n{findings_list}")

    return "\n\n".join(blocks) if blocks else "(no findings available for this section)"


def _build_outline_summary(outline: ReportOutline) -> str:
    lines = [
        f"{s.order}. {s.title} — {s.description}"
        for s in sorted(outline.sections, key=lambda s: s.order)
    ]
    return "\n".join(lines)


async def generate_outline(
    outline_agent: Agent, goal: str, results: dict[str, TaskResult]
) -> ReportOutline:
    summaries_block = _build_summaries_block(results)
    prompt = OUTLINE_PROMPT_TEMPLATE.format(goal=goal, summaries_block=summaries_block)
    result = await outline_agent.run(prompt)
    return result.output


async def write_section(
    section_writer_agent: Agent,
    goal: str,
    outline: ReportOutline,
    section: ReportSection,
    results: dict[str, TaskResult],
) -> str:
    findings_block = _build_findings_block(section.relevant_task_ids, results)
    outline_summary = _build_outline_summary(outline)

    prompt = SECTION_WRITER_PROMPT_TEMPLATE.format(
        goal=goal,
        outline_summary=outline_summary,
        section_title=section.title,
        section_description=section.description,
        findings_block=findings_block,
    )
    result = await section_writer_agent.run(prompt)
    return result.output
