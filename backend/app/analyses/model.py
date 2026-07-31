"""
SQLAlchemy model definitions for persisted AI resume analyses.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.resumes.model import Resume


class AnalysisStatus(str, PyEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResumeAnalysis(Base):
    """
    Stores AI-generated resume analyses.

    One resume can have multiple analysis versions.
    Only one record should have is_latest=True.
    """

    __tablename__ = "resume_analyses"

    # -----------------------------
    # Primary Key
    # -----------------------------

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # -----------------------------
    # Relationships
    # -----------------------------

    resume_id: Mapped[int] = mapped_column(
        ForeignKey(
            "resumes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    resume: Mapped["Resume"] = relationship(
        back_populates="analyses",
    )

    # -----------------------------
    # Version Control
    # -----------------------------

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    is_latest: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # -----------------------------
    # AI Metadata
    # -----------------------------

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    prompt_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="v1",
    )

    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus),
        nullable=False,
        default=AnalysisStatus.COMPLETED,
    )

    processing_time_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # -----------------------------
    # AI Results
    # -----------------------------

    ats_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    career_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    experience_level: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    skills: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    missing_skills: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    strengths: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    weaknesses: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    suggestions: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # -----------------------------
    # Timestamps
    # -----------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # -----------------------------
    # Representation
    # -----------------------------

    def __repr__(self) -> str:
        return (
            f"<ResumeAnalysis("
            f"id={self.id}, "
            f"resume_id={self.resume_id}, "
            f"version={self.version}, "
            f"ats_score={self.ats_score})>"
        )