"""SQLAlchemy model definitions for the AI Career Mentor."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.users.model import User


class ChatRole(str, Enum):
    """
    Supported message roles.

    SYSTEM:
        Internal prompt supplied to the LLM.

    USER:
        Human message.

    ASSISTANT:
        AI response.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(Base):
    """
    Persistent chat history.

    Every authenticated user owns one continuous conversation.
    Messages are stored chronologically and reused as
    conversational memory for future prompts.
    """

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role: Mapped[ChatRole] = mapped_column(
        SqlEnum(
            ChatRole,
            name="chat_role",
            values_callable=lambda enum_class: [
                role.value
                for role in enum_class
            ],
        ),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="chat_messages",
    )

    def __repr__(self) -> str:
        return (
            f"<ChatMessage("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"role='{self.role.value}'"
            f")>"
        )