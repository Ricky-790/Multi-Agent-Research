from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from agents_service.models import ResearchPlan, TaskStatus
from backend.db.models import Task


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- writes ---

    async def create_tasks_from_plan(
        self, report_id: UUID, plan: ResearchPlan
    ) -> None:
        """
        Bulk-insert all Task rows derived from a ResearchPlan in one go.

        Every task is created with status=PENDING. Existing tasks for the same
        report_id are not touched; callers should ensure this is only called once
        per report.
        """
        rows = [
            Task(
                id=task.id,
                report_id=report_id,
                task_name=task.name,
                objective=task.objective,
                depends_on=task.depends_on,
                status=TaskStatus.PENDING.value,
            )
            for task in plan.tasks
        ]
        self.session.add_all(rows)
        await self.session.commit()

    async def update_task_status(
        self, report_id: UUID, task_id: str, status: str
    ) -> None:
        """Update the status of a single task identified by (report_id, task_id)."""
        await self.session.execute(
            update(Task)
            .where(Task.report_id == report_id, Task.id == task_id)
            .values(status=status)
        )
        await self.session.commit()

    async def save_task_result(
        self, report_id: UUID, task_id: str, result: dict
    ) -> None:
        """Persist the JSON result dict for a completed task."""
        await self.session.execute(
            update(Task)
            .where(Task.report_id == report_id, Task.id == task_id)
            .values(result=result)
        )
        await self.session.commit()

    # --- reads ---

    async def get_tasks_by_report(self, report_id: UUID) -> list[Task]:
        """Return all tasks belonging to a report, ordered by creation time."""
        result = await self.session.execute(
            select(Task)
            .where(Task.report_id == report_id)
            .order_by(Task.created_at)
        )
        return list(result.scalars().all())

    async def get_task(self, report_id: UUID, task_id: str) -> Task | None:
        """Return a single task by composite key (report_id, task_id), or None."""
        result = await self.session.execute(
            select(Task).where(Task.report_id == report_id, Task.id == task_id)
        )
        return result.scalar_one_or_none()
