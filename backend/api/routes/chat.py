import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agents_service.agents import classify_query
from agents_service.agents.classifier_agent import classify_query_stream
from agents_service.models import IntentEnum
from backend.api.deps import AuthenticatedUser, get_current_user
from backend.api.dto_models import ChatRequest, ChatResponse, NewChatResponse
from backend.api.utils import db_messages_to_model_messages
from backend.celery_app.tasks import run_research_pipeline_task
from backend.db.services import message_service, reports_service
from backend.db.session import get_session
from custom_logger import get_logger

logger = get_logger()
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
    model_message_history=None
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
        conversation_history = await message_service.get_conversation_messages(
            session=session, conversation_id=conversation_id, user_id=user.user_id
        )
        model_message_history = db_messages_to_model_messages(conversation_history)
    user_message = await message_service.add_message(
        session=session,
        conversation_id=conversation_id,
        role="User",
        message_content=payload.message,
    )
    # Tell frontend user_message is sent -> Show user chat bubble
    if payload.conversation_id is None:
        yield {
            "event": "conversation_created",
            "data": json.dumps(
                {
                    "conversation_id": str(conversation_id),
                }
            ),
        }
    yield {
        "event": "user_message_created",
        "data": json.dumps(
            {
                "id": str(user_message.id),
                "conversation_id": str(conversation_id),
                "role": user_message.role,
                "content": user_message.message_content,
                "sequence_no": user_message.sequence_no,
                "created_at": user_message.created_at.isoformat(),
            }
        ),
    }
    yield {
        "event": "starting_response_stream",
        "data": "",
    }
    final_response = ""
    async for chunk in classify_query_stream(
        query=payload.message, message_history=model_message_history
    ):
        final_response = chunk
        yield {
            "event": "message_delta",
            "data": chunk,
        }
    assistant_message = await message_service.add_message(
        session=session,
        conversation_id=conversation_id,
        role="Agent",
        message_content=final_response,
    )
    # Ping streaming complete
    yield {
        "event": "message_complete",
        "data": json.dumps(
            {
                "id": str(assistant_message.id),
                "conversation_id": str(conversation_id),
                "role": assistant_message.role,
                "content": assistant_message.message_content,
                "sequence_no": assistant_message.sequence_no,
                "created_at": assistant_message.created_at.isoformat(),
            }
        ),
    }
    yield {
        "event": "done",
        "data": "",
    }
