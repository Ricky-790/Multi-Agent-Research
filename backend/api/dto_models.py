from pydantic import BaseModel
from agents_service.models import IntentEnum


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    message: str
    intent: IntentEnum
