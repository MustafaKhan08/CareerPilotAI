"""SQLAlchemy models for the Interview Preparation module."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.database import Base

if TYPE_CHECKING:
    from app.resumes.model import Resume
    from app.users.model import User


# ==========================================================
# ENUMS
# ==========================================================


class InterviewType(str, Enum):
    """Supported interview categories."""

    HR = "hr"
    TECHNICAL = "technical"
    RESUME = "resume"
    BEHAVIORAL = "behavioral"
    MIXED = "mixed"


class InterviewDifficulty(str, Enum):
    """Supported interview difficulty levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class InterviewStatus(str, Enum):
    """Interview lifecycle."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# ==========================================================
# INTERVIEW SESSION
# ==========================================================


class InterviewSession(Base):
    """Represents one complete interview."""

    __tablename__ = "interview_sessions"

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

    resume_id: Mapped[int] = mapped_column(
        ForeignKey(
            "resumes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    interview_type: Mapped[InterviewType] = mapped_column(
        SQLEnum(
            InterviewType,
            name="interview_type",
            values_callable=lambda obj: [
                e.value for e in obj
            ],
            create_type=False,
        ),
        nullable=False,
    )

    difficulty: Mapped[InterviewDifficulty] = mapped_column(
        SQLEnum(
            InterviewDifficulty,
            name="interview_difficulty",
            values_callable=lambda obj: [
                e.value for e in obj
            ],
            create_type=False,
        ),
        nullable=False,
    )

    target_role: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    current_question_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    status: Mapped[InterviewStatus] = mapped_column(
        SQLEnum(
            InterviewStatus,
            name="interview_status",
            values_callable=lambda obj: [
                e.value for e in obj
            ],
            create_type=False,
        ),
        nullable=False,
        default=InterviewStatus.PENDING,
        index=True,
    )

    overall_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    recommendations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship()

    resume: Mapped["Resume"] = relationship()

    questions: Mapped[list["InterviewQuestion"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.question_order",
    )


# ==========================================================
# QUESTIONS
# ==========================================================


class InterviewQuestion(Base):
    """One interview question."""

    __tablename__ = "interview_questions"

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "question_order",
            name="uq_interview_question_order",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "interview_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    session: Mapped["InterviewSession"] = relationship(
        back_populates="questions",
    )

    answer: Mapped["InterviewAnswer | None"] = relationship(
        back_populates="question",
        uselist=False,
        cascade="all, delete-orphan",
    )


# ==========================================================
# ANSWERS
# ==========================================================


class InterviewAnswer(Base):
    """User answer plus AI evaluation."""

    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey(
            "interview_questions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    evaluation: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    question: Mapped["InterviewQuestion"] = relationship(
        back_populates="answer",
    )