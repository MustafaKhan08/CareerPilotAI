"""Pydantic request and response schemas for the resume domain."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResumeCreate(BaseModel):
    """Validate metadata recorded after a resume file is saved to disk."""

    user_id: int = Field(gt=0)
    original_filename: str = Field(min_length=1, max_length=255)
    stored_filename: str = Field(min_length=1, max_length=255)
    file_path: str = Field(min_length=1, max_length=500)
    file_type: str = Field(min_length=1, max_length=100)
    extracted_text: str = Field(min_length=1)


class ResumeResponse(BaseModel):
    """Expose persisted resume metadata after upload."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_filename: str
    stored_filename: str
    file_path: str
    file_type: str
    created_at: datetime
    updated_at: datetime


class ResumeListResponse(BaseModel):
    """Expose resume information when listing user resumes."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    file_type: str
    created_at: datetime
    updated_at: datetime