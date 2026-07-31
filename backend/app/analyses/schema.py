"""
Pydantic schemas for Resume Analysis.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AnalysisStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ==========================================================
# Base Schema
# ==========================================================

class ResumeAnalysisBase(BaseModel):
    ats_score: int = Field(..., ge=0, le=100)

    career_domain: str

    experience_level: str

    summary: str

    skills: List[str]

    missing_skills: List[str]

    strengths: List[str]

    weaknesses: List[str]

    suggestions: List[str]


# ==========================================================
# Create Schema
# ==========================================================

class ResumeAnalysisCreate(ResumeAnalysisBase):

    resume_id: int

    version: int = 1

    is_latest: bool = True

    provider: str

    model_name: str

    model_version: Optional[str] = None

    prompt_version: str = "v1"

    analysis_status: AnalysisStatus = AnalysisStatus.COMPLETED

    processing_time_ms: Optional[float] = None


# ==========================================================
# Update Schema
# ==========================================================

class ResumeAnalysisUpdate(BaseModel):

    is_latest: Optional[bool] = None

    analysis_status: Optional[AnalysisStatus] = None

    processing_time_ms: Optional[float] = None

    ats_score: Optional[int] = Field(None, ge=0, le=100)

    career_domain: Optional[str] = None

    experience_level: Optional[str] = None

    summary: Optional[str] = None

    skills: Optional[List[str]] = None

    missing_skills: Optional[List[str]] = None

    strengths: Optional[List[str]] = None

    weaknesses: Optional[List[str]] = None

    suggestions: Optional[List[str]] = None


# ==========================================================
# Response Schema
# ==========================================================

class ResumeAnalysisResponse(ResumeAnalysisBase):

    id: int

    resume_id: int

    version: int

    is_latest: bool

    provider: str

    model_name: str

    model_version: Optional[str]

    prompt_version: str

    analysis_status: AnalysisStatus

    processing_time_ms: Optional[float]

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================================
# Lightweight Summary Schema
# ==========================================================

class ResumeAnalysisSummary(BaseModel):

    id: int

    version: int

    ats_score: int

    is_latest: bool

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)