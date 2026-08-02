from fastapi import APIRouter, Depends
from agents_service.agents import classify_query
from agents_service.models import IntentEnum
from backend.api.dto_models import ChatRequest, ChatResponse
from backend.db.session import get_session
from backend.db.services.user_report_service import reports_service
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


@router.post("/chat")
async def send_message(
    payload: ChatRequest, session: AsyncSession = Depends(get_session)
):
    classification = await classify_query(payload.query)
    categories = [c.value for c in classification.categories]

    report = await reports_service.create_report(user_id, payload.query)
    await reports_service.save_classification(
        report.id, classification.intent.value, categories, classification.response
    )

    if classification.intent != IntentEnum.RESEARCH_TOPIC:
        await reports_service.update_status(report.id, "done")
        return ChatResponse(
            message=classification.response, intent=classification.intent
        )

    await reports_service.update_status(report.id, "pending")

    run_research_pipeline_task.delay(str(report.id))
    return ChatResponse(message=classification.response, intent=classification.intent)
