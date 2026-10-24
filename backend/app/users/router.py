"""HTTP endpoints for the user domain."""

from typing import Annotated
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, get_current_user
from app.db.database import get_db
from app.email_tokens.model import TokenPurpose
from app.email_tokens.schema import (
    ForgotPasswordRequest,
    MessageResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
)
from app.email_tokens.service import consume_token, create_token
from app.users.model import User
from app.users.schema import UserCreate, UserLogin, UserResponse
from app.users.service import authenticate_user, create_user, get_user_by_email

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Existing endpoints (unchanged)
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Register a new user and send an email-verification message."""

    try:
        user = create_user(db, user_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Send verification email (best-effort on registration; log failures but
    # never block user creation â€” they can resend from the login page).
    try:
        from app.email_tokens.email_service import send_verification_email

        raw_token = create_token(
            db, user_id=user.id, purpose=TokenPurpose.EMAIL_VERIFICATION
        )
        send_verification_email(to=user.email, token=raw_token)
    except RuntimeError as email_exc:
        _logger.error(
            "Verification email not sent for new user (id=%s): %s",
            user.id,
            email_exc,
        )
    except Exception as email_exc:
        _logger.error(
            "Unexpected error sending verification email for user id=%s: %s",
            user.id,
            email_exc,
        )

    return UserResponse.model_validate(user)


@router.post("/login")
def login_user(
    credentials: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Authenticate credentials and return a JWT."""


    try:
        user = authenticate_user(
            db,
            credentials.email,
            credentials.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/token")
def login_for_swagger(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    """Issue a JWT for Swagger's Authorize button."""


    try:
        user = authenticate_user(
            db,
            form_data.username,
            form_data.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get(
    "/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Return the authenticated user's profile."""

    return UserResponse.model_validate(current_user)


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------


@router.get(
    "/verify-email",
    response_model=MessageResponse,
)
def verify_email(
    token: Annotated[str, Query(min_length=1)],
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    """Consume a verification token and mark the user's email as verified."""

    record = consume_token(
        db, raw_token=token, purpose=TokenPurpose.EMAIL_VERIFICATION
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link.",
        )

    from app.users.service import get_user_by_id

    user = get_user_by_id(db, record.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    user.is_email_verified = True
    db.commit()

    return MessageResponse(message="Email verified successfully.")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
)
def resend_verification(
    body: ResendVerificationRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    """Resend the email-verification link.

    Always returns the same generic response to prevent email enumeration.
    """

    _GENERIC = "If that email is registered and unverified, a new link has been sent."

    user = get_user_by_email(db, body.email)

    if user is None or user.is_email_verified:
        return MessageResponse(message=_GENERIC)

    try:
        from app.email_tokens.email_service import send_verification_email

        raw_token = create_token(
            db, user_id=user.id, purpose=TokenPurpose.EMAIL_VERIFICATION
        )
        send_verification_email(to=user.email, token=raw_token)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return MessageResponse(message=_GENERIC)


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
)
def forgot_password(
    body: ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    """Send a password-reset email.

    Always returns the same generic response to prevent email enumeration.
    """

    _GENERIC = (
        "If that email is registered, a password-reset link has been sent."
    )

    user = get_user_by_email(db, body.email)

    if user is None:
        return MessageResponse(message=_GENERIC)

    try:
        from app.email_tokens.email_service import send_password_reset_email

        raw_token = create_token(
            db, user_id=user.id, purpose=TokenPurpose.PASSWORD_RESET
        )
        send_password_reset_email(to=user.email, token=raw_token)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return MessageResponse(message=_GENERIC)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    body: ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    """Consume a reset token and update the user's password."""

    record = consume_token(
        db, raw_token=body.token, purpose=TokenPurpose.PASSWORD_RESET
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset link.",
        )

    from app.users.service import get_user_by_id
    from pwdlib import PasswordHash

    user = get_user_by_id(db, record.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    password_hasher = PasswordHash.recommended()
    user.password_hash = password_hasher.hash(body.new_password)
    db.commit()

    return MessageResponse(message="Password reset successfully. You can now sign in.")
