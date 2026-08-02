from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import UserReport, RunStatus


class UserReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- writes ---

    async def create_report(self, user_id: UUID, goal: str) -> UserReport:
        """Create a new UserReport with PENDING status and return it."""
        report = UserReport(
            user_id=user_id,
            goal=goal,
            status=RunStatus.PENDING,
        )
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def update_status(self, report_id: UUID, status: str) -> None:
        """Update the status field of an existing report."""
        await self.session.execute(
            update(UserReport)
            .where(UserReport.id == report_id)
            .values(status=status)
        )
        await self.session.commit()

    async def save_classification(
        self,
        report_id: UUID,
        intent: str,
        categories: list[str] | None,
        response: str | None,
    ) -> None:
        """Persist classifier output (intent, categories, response) onto a report."""
        await self.session.execute(
            update(UserReport)
            .where(UserReport.id == report_id)
            .values(intent=intent, categories=categories, response=response)
        )
        await self.session.commit()

    async def save_plan_metadata(
        self, report_id: UUID, strategy_summary: str
    ) -> None:
        """Persist the planner's strategy summary onto a report."""
        await self.session.execute(
            update(UserReport)
            .where(UserReport.id == report_id)
            .values(strategy_summary=strategy_summary)
        )
        await self.session.commit()

    async def save_report_content(
        self, report_id: UUID, title: str, content: str
    ) -> None:
        """Persist the synthesised report title and markdown content."""
        await self.session.execute(
            update(UserReport)
            .where(UserReport.id == report_id)
            .values(report_title=title, report_content=content)
        )
        await self.session.commit()

    async def delete_report(self, report_id: UUID, user_id: UUID) -> bool:
        """
        Delete a report owned by the given user.

        Returns True if a row was deleted, False if no matching row was found.
        """
        result = await self.session.execute(
            select(UserReport).where(
                UserReport.id == report_id, UserReport.user_id == user_id
            )
        )
        report = result.scalar_one_or_none()
        if report is None:
            return False
        await self.session.delete(report)
        await self.session.commit()
        return True

    # --- reads ---

    async def get_report_by_id(self, report_id: UUID) -> UserReport | None:
        """Return the UserReport with the given id, or None if not found."""
        result = await self.session.execute(
            select(UserReport).where(UserReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def get_reports_by_user(
        self, user_id: UUID, limit: int, offset: int
    ) -> list[UserReport]:
        """Return a paginated list of reports belonging to a user, newest first."""
        result = await self.session.execute(
            select(UserReport)
            .where(UserReport.user_id == user_id)
            .order_by(UserReport.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_report_status(self, report_id: UUID) -> str | None:
        """Return just the status string for a report, or None if not found."""
        result = await self.session.execute(
            select(UserReport.status).where(UserReport.id == report_id)
        )
        return result.scalar_one_or_none()
