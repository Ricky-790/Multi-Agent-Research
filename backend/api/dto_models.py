from pydantic import BaseModel
from agents_service.models import IntentEnum
from uuid import UUID


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    message: str
    intent: IntentEnum


class ChatResponse(BaseModel):
    message: str
    intent: IntentEnum
    report_id: UUID | None = None
