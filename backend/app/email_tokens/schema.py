"""Pydantic schemas for email-verification and password-reset flows."""

from pydantic import BaseModel, EmailStr, Field


class MessageResponse(BaseModel):
    """Generic single-message response used by all email-flow endpoints."""

    message: str


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


class ResendVerificationRequest(BaseModel):
    """Request body for POST /users/resend-verification."""

    email: EmailStr


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


class ForgotPasswordRequest(BaseModel):
    """Request body for POST /users/forgot-password."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request body for POST /users/reset-password."""

    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)
