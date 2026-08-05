from typing import Literal
from uuid import UUID

from fastapi import WebSocket
from pydantic import BaseModel

from agents_service.models import IntentEnum


# Chat route
class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    message: str
    intent: IntentEnum
    report_id: UUID | None = None


# Reports route


class PublishMessage(BaseModel):
    phase: str
    status: Literal["Starting", "Finished"]
    done: bool = False


class ConnectionManager:
    """Wrapper class to handle Ws connections"""

    def __init__(self):
        self.connections: dict[UUID, WebSocket] = {}

    async def connect(self, report_id: UUID, websocket: WebSocket):
        await websocket.accept()
        self.connections[report_id] = websocket

    def disconnect(self, report_id: UUID):
        self.connections.pop(report_id, None)

    async def send(self, report_id, message: PublishMessage):
        websocket = self.connections.get(report_id)
        if websocket:
            await websocket.send_json(message.model_dump(mode="json"))
