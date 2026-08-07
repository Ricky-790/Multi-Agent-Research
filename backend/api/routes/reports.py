from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dto_models import (
    ConnectionManager,
    PublishMessage,
    ReportResponse,
    ReportStatusResponse,
)
from backend.api.redis_manager import client
from backend.db.models import RunStatus
from backend.db.session import get_session
from backend.db.services.user_report_service import reports_service
from backend.api.deps import get_current_user, AuthenticatedUser, get_current_user_ws

router = APIRouter()
# _report_service = UserReportService()
connection_manager = ConnectionManager()


@router.get(
    "/report/{report_id}",
    response_model=ReportResponse | ReportStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_report(
    report_id: UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReportResponse | ReportStatusResponse:
    report = await reports_service.get_report_by_id(session, report_id)
    if report.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )

    if report.status not in {RunStatus.DONE, RunStatus.FAILED}:
        # response.status_code = status.HTTP_202_ACCEPTED
        return ReportStatusResponse(
            report_id=report.id,
            status=report.status,
        )

    if report.status == RunStatus.DONE:
        return ReportResponse(
            report_id=report.id,
            goal=report.goal,
            intent=report.intent,
            categories=report.categories,
            strategy_summary=report.strategy_summary,
            title=report.report_title,
            content=report.report_content,
            created_at=report.created_at.isoformat(),
            updated_at=report.updated_at.isoformat(),
        )

    # RunStatus.FAILED or any unexpected value
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Report '{report_id}' failed during processing.",
    )


@router.websocket(
    "/ws/{report_id}"
)  # needs a dependency to check if user id has access to report id
async def websocket_endpoint(
    websocket: WebSocket,
    report_id: UUID,
    user: AuthenticatedUser = Depends(get_current_user_ws),
    session: AsyncSession = Depends(get_session),
):
    report = await reports_service.get_report_by_id(session, report_id)
    if report.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
    await connection_manager.connect(report_id, websocket)
    pubsub = client.pubsub()
    await pubsub.subscribe(f"report:{report_id}")
    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,  # Ignore internal generated messages
                timeout=1,
            )

            if message:
                publish_message = PublishMessage.model_validate_json(
                    message["data"].decode()
                )

                await connection_manager.send(
                    report_id,
                    publish_message,
                )
                if publish_message.done:
                    await websocket.close()
                    break

    except WebSocketDisconnect:
        connection_manager.disconnect(report_id)
    finally:
        connection_manager.disconnect(report_id)
        await pubsub.unsubscribe(f"report:{report_id}")
        await pubsub.close()
