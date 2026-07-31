from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskResultStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class Source(BaseModel):
    url: str = Field(..., description="The URL of the source used.")
    title: Optional[str] = Field(
        default=None, description="The title of the source page, if available."
    )


class KeyFinding(BaseModel):
    point: str = Field(
        ...,
        description="One distinct, self-contained finding relevant to the task's objective. Should be specific and factual, not vague.",
    )
    supporting_detail: Optional[str] = Field(
        default=None,
        description="Additional context, numbers, or explanation backing this finding, if needed.",
    )
    source_urls: list[str] = Field(
        default_factory=list,
        description="URLs (from the sources list) that support this specific finding",
    )


class TaskResult(BaseModel):
    task_id: str = Field(
        ..., description="The id of the Task this result corresponds to."
    )
    status: TaskResultStatus = Field(
        ...,
        description="'success' if the task was completed, 'partial' if some information could not be found, 'failed' if the task could not be meaningfully completed.",
    )
    summary: str = Field(
        ...,
        description="A short (2-4 sentence) narrative summary of what was found, giving a reader the gist without needing the full findings list.",
    )
    key_findings: list[KeyFinding] = Field(
        default=[],
        description="The distinct, structured findings gathered for this task's objective. This is the primary content the synthesizer will draw on.",
    )
    sources: list[Source] = Field(
        default_factory=list,
        description="All sources consulted while completing this task.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional notes on limitations, contradictions between sources, or gaps in available information — useful context for the synthesizer, not for the reader.",
    )
