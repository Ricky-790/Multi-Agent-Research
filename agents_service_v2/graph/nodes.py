import logging
from typing import Any

from langgraph.types import Send, StreamWriter

from agents_service.agents import (
    create_research_plan,
    generate_outline,
    get_outline_agent,
    get_section_writer_agent,
    get_subagent,
    write_section,
)
from agents_service.models import (
    Report,
    ReportOutline,
    ResearchPlan,
    TaskResult,
    TaskResultStatus,
)
from agents_service.pipeline.rate_limiting import run_with_retry
from agents_service_v2.graph.state import (
    ResearchGraphState,
    ResearchPhaseState,
    SectionWriteState,
)

logger = logging.getLogger(__name__)


# ─── Node: Decompose (Graph Entry Point) ─────────────────────────


async def decompose_node(state: ResearchGraphState, writer: StreamWriter) -> dict:
    """Generate the research plan (DAG). This is now the graph entry point."""
    writer({"event": "stage", "phase": "planning", "status": "starting"})

    plan: ResearchPlan = await create_research_plan(state["query"], state["categories"])
    logger.info(f"Plan generated with {len(plan.tasks)} tasks")

    writer(
        {
            "event": "stage",
            "phase": "planning",
            "status": "finished",
            "strategy_summary": plan.strategy_summary,
            "task_count": len(plan.tasks),
        }
    )

    return {"plan": plan}


# ─── Research Subgraph: Entry ────────────────────────────────────


async def research_supervisor_node(
    state: ResearchPhaseState, writer: StreamWriter
) -> dict:
    """
    Initializes the research phase subgraph state.
    This runs inside the subgraph, receiving the subgraph's state schema.
    """
    writer({"event": "stage", "phase": "research", "status": "starting"})

    plan = state["plan"]
    pending = [t.id for t in plan.tasks]

    return {
        "plan": plan,
        "done": {},
        "pending": pending,
        "just_completed": [],
        "error": None,
        "stream_events": [],
    }


# ─── Research Subgraph: Dispatcher (checkpoint) ──────────────────


async def research_dispatcher(state: ResearchPhaseState, writer: StreamWriter) -> dict:
    """
    Checkpoint node before the conditional edge that actually routes.
    The routing logic (who is ready) lives in the conditional edge function in graph.py.
    """
    return {}


# ─── Research Subgraph: Execute Single Task ──────────────────────


async def execute_task_node(state: dict, writer: StreamWriter) -> dict:
    """
    Executes a single research task. Invoked via Send from the conditional edge.
    The `state` argument here is whatever payload the Send carried.
    """
    from agents_service.agents.subagent import execute_task as run_subagent_task

    task = state["task"]
    done = state["done"]
    subagent = get_subagent()

    logger.info(f"Starting task {task.id}: {task.name}")
    writer(
        {"event": "task", "task_id": task.id, "status": "running", "name": task.name}
    )

    try:
        result = await run_with_retry(run_subagent_task, subagent, task, done)
    except Exception as e:
        logger.exception(f"Task {task.id} failed after retries")
        result = TaskResult(
            task_id=task.id,
            status=TaskResultStatus.FAILED,
            summary=f"Task failed: {e}",
            key_findings=[],
            sources=[],
            notes=str(e),
        )

    logger.info(f"Finished task {task.id} with status={result.status}")
    writer(
        {
            "event": "task",
            "task_id": task.id,
            "status": result.status.value,
            "name": task.name,
            "result": result.model_dump(mode="json"),
        }
    )

    return {
        "done": {task.id: result},
        "just_completed": [task.id],
    }


# ─── Research Subgraph: Gather ───────────────────────────────────


async def research_gather_node(state: ResearchPhaseState, writer: StreamWriter) -> dict:
    """
    Removes completed tasks from pending list after a parallel batch finishes.
    If nothing remains, streams the research-finished event.
    """
    completed = set(state["just_completed"])
    pending = [tid for tid in state["pending"] if tid not in completed]

    if not pending:
        writer({"event": "stage", "phase": "research", "status": "finished"})

    return {
        "pending": pending,
        "just_completed": [],
    }


# ─── Node: Generate Outline ──────────────────────────────────────


async def synthesize_outline_node(
    state: ResearchGraphState, writer: StreamWriter
) -> dict:
    """Creates the report outline from research findings."""
    writer({"event": "stage", "phase": "synthesis", "status": "starting"})

    outline_agent = get_outline_agent()
    outline = await run_with_retry(
        generate_outline, outline_agent, state["query"], state["task_results"]
    )
    logger.info(f"Outline generated with {len(outline.sections)} sections")

    writer(
        {
            "event": "stage",
            "phase": "synthesis",
            "status": "outline_ready",
            "section_count": len(outline.sections),
        }
    )

    return {"report_outline": outline}


# ─── Conditional Edge: Dispatch Section Writers ──────────────────


def dispatch_section_writers(state: ResearchGraphState):
    """
    Conditional edge function.
    Returns a list of Send objects — one per section — so LangGraph runs them in parallel.
    """
    outline = state["report_outline"]
    results = state["task_results"]
    goal = state["query"]

    return [
        Send(
            "write_section_node",
            {
                "goal": goal,
                "outline": outline,
                "section": section,
                "results": results,
                "order": section.order,
            },
        )
        for section in outline.sections
    ]


# ─── Node: Write Single Section ──────────────────────────────────


async def write_section_node(state: SectionWriteState, writer: StreamWriter) -> dict:
    """Writes one report section. Invoked via Send for parallel execution."""
    section = state["section"]
    section_writer = get_section_writer_agent()

    logger.info(f"Writing section {section.order}: {section.title}")
    writer(
        {
            "event": "section",
            "order": section.order,
            "status": "writing",
            "title": section.title,
        }
    )

    content = await run_with_retry(
        write_section,
        section_writer,
        state["goal"],
        state["outline"],
        section,
        state["results"],
    )

    writer(
        {
            "event": "section",
            "order": section.order,
            "status": "completed",
            "title": section.title,
        }
    )

    return {"written_sections": {section.order: content}}


# ─── Node: Compile Report ────────────────────────────────────────


def compile_report_node(state: ResearchGraphState, writer: StreamWriter) -> dict:
    """Assembles final markdown report from written sections."""
    outline = state["report_outline"]
    sections = state["written_sections"]

    written = []
    for section in sorted(outline.sections, key=lambda s: s.order):
        content = sections.get(section.order, "")
        written.append(f"## {section.title}\n\n{content}")

    full_content = f"# {outline.title}\n\n" + "\n\n".join(written)
    report = Report(title=outline.title, content=full_content)

    logger.info(f"Report generated: '{report.title}' ({len(report.content)} chars)")
    writer({"event": "stage", "phase": "synthesis", "status": "finished"})

    return {"final_report": report}
