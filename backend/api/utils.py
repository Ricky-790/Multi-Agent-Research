from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from backend.db.models import Messages


def db_messages_to_model_messages(messages: list[Messages]) -> list[ModelMessage]:
    model_messages: list[ModelMessage] = []

    for msg in sorted(messages, key=lambda m: m.sequence_no):
        if msg.role == "User":
            model_messages.append(
                ModelRequest(parts=[UserPromptPart(content=msg.message_content)])
            )
        elif msg.role == "Agent":
            model_messages.append(
                ModelResponse(parts=[TextPart(content=msg.message_content)])
            )
        # any other role (e.g. "system") — extend here if you ever store those

    return model_messages
