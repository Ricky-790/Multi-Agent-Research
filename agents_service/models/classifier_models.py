from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class IntentEnum(str, Enum):
    GREETING = "greeting"  # "hi", "hello", "hey there"
    SIMPLE_QUESTION = "simple_question"  # answerable directly
    RESEARCH_TOPIC = "research_topic"  # needs the full pipeline
    UNSUPPORTED = "unsupported"  # irrelevant or out of scope


class CategoryEnum(str, Enum):
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    SCIENTIFIC_OR_ACADEMIC = "scientific_or_academic"
    PERSON = "person"
    HISTORIC_EVENT = "historic_event"
    GENERAL = "general"


class IntentClassification(BaseModel):
    intent: IntentEnum
    response: str = Field(
        ...,
        description="A short, ready-to-send response for the user, appropriate to the classified intent.",
    )
    categories: list[CategoryEnum] = Field(
        default_factory=list,
        description="ONLY populated for RESEARCH_TOPIC. One or more categories that best describe the topic's domain(s). Use multiple when the topic is genuinely interdisciplinary (e.g. NVIDIA -> [person, technology, finance]). Empty list for GREETING or UNSUPPORTED.",
    )
    research_topic: Optional[str] = Field(
        default=None,
        description="ONLY populated for intent = RESEARCH_TOPIC. This is a detailed statement of the research topic, specific to the user's request, inferred from all messages in the conversation",
    )

    @model_validator(mode="after")
    def validate_research_topic(self) -> "IntentClassification":
        if self.intent == IntentEnum.RESEARCH_TOPIC and self.research_topic is None:
            raise ValueError(
                f"Need a `research_topic` when `intent=research_topic`, but `research_topic` not provided."
            )
        return self
