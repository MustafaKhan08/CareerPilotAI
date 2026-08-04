"""Pydantic schemas for the AI Career Mentor."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ChatRequest(BaseModel):
    """
    Validate an incoming user message.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message sent to the AI Career Mentor.",
    )


class ChatResponse(BaseModel):
    """
    Assistant response returned to the client.
    """

    role: Literal["assistant"] = "assistant"

    message: str


class ChatMessageResponse(BaseModel):
    """
    Single persisted chat message.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    user_id: int

    role: Literal[
        "system",
        "user",
        "assistant",
    ]

    message: str

    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """
    Complete persistent conversation history.
    """

    messages: list[ChatMessageResponse]