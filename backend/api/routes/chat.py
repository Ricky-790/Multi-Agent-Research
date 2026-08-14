from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agents_service.agents import classify_query
from agents_service.models import IntentEnum
from backend.api.deps import AuthenticatedUser, get_current_user
from backend.api.dto_models import ChatRequest, ChatResponse
from backend.celery_app.tasks import run_research_pipeline_task
from backend.db.services.user_report_service import reports_service
from backend.db.session import get_session

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    classification = await classify_query(query=payload.query)
    categories = [c.value for c in classification.categories]

    report = await reports_service.create_report(session, user.user_id, payload.query)
    await reports_service.save_classification(
        session,
        report.id,
        classification.intent.value,
        categories,
        classification.response,
    )

    if classification.intent != IntentEnum.RESEARCH_TOPIC:
        await reports_service.update_status(session, report.id, "done")
        return ChatResponse(
            message=classification.response,
            intent=classification.intent,
            report_id=None,
        )

    await reports_service.update_status(session, report.id, "pending")
    print(type(report.id))
    run_research_pipeline_task.delay(str(report.id))

    return ChatResponse(
        message=classification.response,
        intent=classification.intent,
        report_id=report.id,
    )
