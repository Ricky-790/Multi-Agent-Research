import asyncio
import logging
from uuid import UUID

from agents_service.agents.classifier_agent import classify_query
from agents_service.agents.decomposer_agent import create_research_plan
from agents_service.models import IntentEnum
from agents_service.pipeline.create_report import generate_report
from agents_service.pipeline.executor import execute_research_phase
from backend.api.dto_models import PublishMessage
from backend.api.redis_manager import client
from backend.celery_app.config import celery_app
from backend.db.services.task_service import tasks_service
from backend.db.services.user_report_service import reports_service
from backend.db.session import async_session_factory

logger = logging.getLogger(__name__)


@celery_app.task(name="run_research_pipeline", bind=True, max_retries=0)
def run_research_pipeline_task(self, report_id: str):
    """
    Celery entrypoint. Celery tasks are synchronous by default; this wraps
    our async pipeline in a fresh event loop for this worker execution.
    """
    try:
        asyncio.run(_run_and_persist(UUID(report_id)))
    except Exception:
        logger.exception(f"Pipeline failed for report_id={report_id}")
        asyncio.run(_mark_failed(UUID(report_id)))
        raise


async def _mark_failed(report_id: UUID) -> None:
    async with async_session_factory() as session:
        await reports_service.update_status(session, report_id, "failed")


async def _run_and_persist(report_id: UUID) -> None:
    async with async_session_factory() as session:
        report = await reports_service.get_report_by_id(session, report_id)
        if report is None:
            logger.error(f"No report found for report_id={report_id}")
            return

        query = report.goal
        categories = report.categories

        # --- Planning ---
        await client.publish(
            f"report:{report_id}",
            PublishMessage(
                phase="Planning",
                status="Starting",
            ).model_dump_json(),
        )
        await reports_service.update_status(session, report_id, "planning")
        plan = await create_research_plan(query, categories)
        await reports_service.save_plan_metadata(
            session, report_id, plan.strategy_summary
        )
        await tasks_service.create_tasks_from_plan(session, report_id, plan)
        await client.publish(
            f"report:{report_id}",
            PublishMessage(
                phase="Planning",
                status="Finished",
            ).model_dump_json(),
        )
        # --- Research ---
        await reports_service.update_status(session, report_id, "researching")
        await client.publish(
            f"report:{report_id}",
            PublishMessage(
                phase="Research",
                status="Starting",
            ).model_dump_json(),
        )

        async def on_task_update(task_id: str, status: str, result: dict | None):
            if result is not None:
                await tasks_service.save_task_result(
                    session, report_id, task_id, result
                )
            else:
                await tasks_service.update_task_status(
                    session, report_id, task_id, status
                )

        results = await execute_research_phase(
            plan, max_concurrency=2, on_task_update=on_task_update
        )
        await client.publish(
            f"report:{report_id}",
            PublishMessage(
                phase="Research",
                status="Finished",
            ).model_dump_json(),
        )
        # --- Synthesis ---
        await client.publish(
            f"report:{report_id}",
            PublishMessage(
                phase="Synthesis",
                status="Starting",
            ).model_dump_json(),
        )
        await reports_service.update_status(session, report_id, "synthesizing")
        report_output = await generate_report(query, results)
        await reports_service.save_report_content(
            session, report_id, report_output.title, report_output.content
        )
        await client.publish(
            f"report:{report_id}",
            PublishMessage(
                phase="Synthesis",
                status="Finished",
                done=True
            ).model_dump_json(),
        )
        await reports_service.update_status(session, report_id, "done")
