import asyncio
from uuid import UUID

from agents_service.pipeline import Pipeline
from backend.api.dto_models import PublishMessage
from backend.celery_app import celery_app
from backend.celery_app import pipeline_resources
from backend.db.services.task_service import tasks_service
from backend.db.services.user_report_service import reports_service
from backend.db.models import RunStatus
from custom_logger import get_logger
from typing import Literal

logger = get_logger()


@celery_app.task(name="run_research_pipeline", bind=True, max_retries=0)
def run_research_pipeline_task(self, report_id: str):
    """
    Celery entrypoint. Celery tasks are synchronous by default; this wraps
    our async pipeline in a fresh event loop for this worker execution.
    """
    asyncio.run(run_pipeline(report_id))


async def run_pipeline(report_id: str) -> None:
    async with pipeline_resources() as (session_factory, redis_client):
        report_id_uuid = UUID(report_id)

        async def publish(
            phase: str,
            status: Literal["Starting", "Finished"],
            done: bool = False,
            task: str | None = None,
        ):
            await redis_client.publish(
                f"report:{report_id}",
                PublishMessage(
                    phase=phase, status=status, done=done, task=task
                ).model_dump_json(),
            )

        async def on_task_update(
            task_id: str, status: str, result: dict | None, task: str
        ):
            async with session_factory() as session:
                if result is not None:
                    await tasks_service.save_task_result(
                        session, report_id_uuid, task_id, result
                    )
                else:
                    await tasks_service.update_task_status(
                        session, report_id_uuid, task_id, status
                    )
            await publish(phase="research", task=task, status=status)

        async def on_stage_complete(phase: str, status: str, **extra):
            await publish(phase, status)

            async with session_factory() as session:
                if phase == "planning" and status == "starting":
                    await reports_service.update_status(
                        session, report_id_uuid, "planning"
                    )

                elif phase == "planning" and status == "finished":
                    plan = extra["plan"]
                    await reports_service.save_plan_metadata(
                        session, report_id_uuid, plan.strategy_summary
                    )
                    await tasks_service.create_tasks_from_plan(
                        session, report_id_uuid, plan
                    )
                    await reports_service.update_status(
                        session, report_id_uuid, "researching"
                    )

                elif phase == "research" and status == "finished":
                    await reports_service.update_status(
                        session, report_id_uuid, "synthesizing"
                    )

                elif phase == "synthesis" and status == "finished":
                    report = extra["report"]
                    await reports_service.save_report_content(
                        session, report_id_uuid, report.title, report.content
                    )
                    await reports_service.update_status(session, report_id_uuid, "done")

        pipeline = Pipeline(
            on_task_update=on_task_update, on_stage_complete=on_stage_complete
        )

        try:
            async with session_factory() as session:
                report = await reports_service.get_report_by_id(session, report_id_uuid)
                if report is None:
                    logger.error(f"No report found for report_id={report_id}")
                    return
                query = report.goal
                categories = report.categories

            await pipeline.run_pipeline(query, categories)
            await publish("Full", "Finished", done=True)

        except Exception:
            logger.exception(f"Pipeline failed for report_id={report_id}")
            async with session_factory() as session:
                await reports_service.update_status(session, report_id_uuid, "failed")
            await publish("failed", "error", done=True)
            raise
    # engine + redis_client GUARANTEED disposed here, regardless of how the
    # try/except above exited
