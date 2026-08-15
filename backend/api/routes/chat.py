from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agents_service.agents import classify_query
from agents_service.agents.classifier_agent import classify_query_stream
from agents_service.models import IntentEnum
from backend.api.deps import AuthenticatedUser, get_current_user
from backend.api.dto_models import ChatRequest, ChatResponse, NewChatResponse
from backend.celery_app.tasks import run_research_pipeline_task
from backend.db.services import message_service, reports_service
from backend.db.session import get_session

router = APIRouter()


@router.post("/chat", response_class=EventSourceResponse)
async def send_message(
    payload: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # No conv_id -> create new conv
    # Save message
    # call llm
    # stream response
    conversation_id = payload.conversation_id
    if conversation_id is None:
        conversation_id = await message_service.create_new_conversation(
            session=session, user_id=user.user_id, title=payload.message
        )
    else:
        conversation_exists = await message_service.conversation_exists(
            session=session, conversation_id=conversation_id, user_id=user.user_id
        )
        if not conversation_exists:
            raise HTTPException(
                detail="Conversation not found", status_code=status.HTTP_404_NOT_FOUND
            )
    messages = await message_service.add_message(
        session=session,
        conversation_id=conversation_id,
        role="User",
        message_content=payload.message,
    )
    system_msg = ""
    async for response in classify_query_stream(payload.message):
        system_msg = response
        yield {
            "event": "message",
            "data": response,
        }

    await message_service.add_message(
        session=session,
        conversation_id=conversation_id,
        role="System",
        message_content=system_msg,
    )
    yield {
        "event": "done",
        "data": "",
    }
