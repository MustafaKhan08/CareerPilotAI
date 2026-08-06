"""
Pydantic schemas for the job domain.
"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


# =====================================================
# CREATE
# =====================================================

class JobCreate(BaseModel):
    """
    Validate data required to create a job.
    """

    job_title: str = Field(
        min_length=1,
        max_length=255,
    )

    job_description: str = Field(
        min_length=1,
    )

    combined_text: str = Field(
        min_length=1,
    )

    job_type: str | None = Field(
        default=None,
        max_length=100,
    )

    categories: str | None = None

    location: str | None = None

    city: str | None = None

    state: str | None = None

    country: str | None = None

    salary_from: float | None = Field(
        default=None,
        ge=0,
    )

    salary_to: float | None = Field(
        default=None,
        ge=0,
    )

    salary_period: str | None = None

    apply_url: str | None = None

    apply_email: str | None = None

    employees: int | None = Field(
        default=None,
        ge=0,
    )

    industry: str | None = None

    company_name: str | None = None

    company_description: str | None = None

    crawl_timestamp: datetime | None = None


# =====================================================
# RESPONSE
# =====================================================

class JobResponse(BaseModel):
    """
    Response schema for a job.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    job_title: str

    job_description: str

    combined_text: str

    job_type: str | None

    categories: str | None

    location: str | None

    city: str | None

    state: str | None

    country: str | None

    salary_from: float | None

    salary_to: float | None

    salary_period: str | None

    apply_url: str | None

    apply_email: str | None

    employees: int | None

    industry: str | None

    company_name: str | None

    company_description: str | None

    crawl_timestamp: datetime | None

    created_at: datetime

    updated_at: datetime


# =====================================================
# JOB SUMMARY RESPONSE
# =====================================================

class JobSummaryResponse(BaseModel):
    """
    Lightweight job summary returned by semantic search.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int

    job_title: str

    company_name: str | None

    location: str | None

    job_type: str | None

    salary_from: float | None

    salary_to: float | None

    industry: str | None

    apply_url: str | None

    similarity_score: float


# =====================================================
# PAGINATED RESPONSE
# =====================================================

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated wrapper response.
    """

    items: list[T]

    page: int

    limit: int

    total: int

    total_pages: int