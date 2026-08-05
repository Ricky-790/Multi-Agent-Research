from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.dto_models import ConnectionManager, PublishMessage
from backend.api.redis_manager import client

router = APIRouter()

connection_manager = ConnectionManager()


@router.websocket(
    "/ws/{report_id}"
)  # needs a dependency to check if user id has access to report id
async def websocket_endpoint(websocket: WebSocket, report_id: UUID):
    await connection_manager.connect(report_id, websocket)
    pubsub = client.pubsub()
    await pubsub.subscribe(f"report:{report_id}")
    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, # Ignore internal generated messages
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
