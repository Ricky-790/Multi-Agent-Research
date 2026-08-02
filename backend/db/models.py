import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from agents_service.models import IntentEnum, TaskStatus


class Base(DeclarativeBase):
    pass


class RunStatus:
    PENDING = "pending"
    CLASSIFYING = "classifying"
    PLANNING = "planning"
    RESEARCHING = "researching"
    SYNTHESIZING = "synthesizing"
    DONE = "done"
    FAILED = "failed"


RUN_STATUS_VALUES = [
    RunStatus.PENDING,
    RunStatus.CLASSIFYING,
    RunStatus.PLANNING,
    RunStatus.RESEARCHING,
    RunStatus.SYNTHESIZING,
    RunStatus.DONE,
    RunStatus.FAILED,
]


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    reports: Mapped[list["UserReport"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserReport(Base):
    __tablename__ = "user_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    goal: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(
        SAEnum(*[e.value for e in IntentEnum], name="intent_enum"), nullable=True
    )
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    categories: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(
        SAEnum(*RUN_STATUS_VALUES, name="run_status_enum"),
        nullable=False,
        default=RunStatus.PENDING,
    )

    strategy_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="reports")
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_reports.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    depends_on: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    status: Mapped[str] = mapped_column(
        SAEnum(*[e.value for e in TaskStatus], name="task_status_enum"),
        nullable=False,
        default=TaskStatus.PENDING.value,
    )
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    report: Mapped["UserReport"] = relationship(back_populates="tasks")
