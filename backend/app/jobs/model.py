"""
SQLAlchemy model definitions for the job domain.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Job(Base):
    """
    Represent a job listing stored in the database.
    """

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    job_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    job_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    combined_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    job_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    categories: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    salary_from: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    salary_to: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    salary_period: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    apply_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    apply_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    employees: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    industry: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    company_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    company_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    crawl_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

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