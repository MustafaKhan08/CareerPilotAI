"""Tests for email-verification and password-reset flows.

Uses a shared in-memory SQLite database (StaticPool) so that every connection
within a test sees the same data.  No real emails are sent; Resend is stubbed.
"""

import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Import models BEFORE anything that touches Base.metadata so that every
# table is registered before create_all() is called.
# ---------------------------------------------------------------------------
from app.db.database import Base, get_db  # noqa: E402
from app.users.model import User  # noqa: F401, E402
from app.email_tokens.model import EmailToken, TokenPurpose  # noqa: F401, E402

# Import app last (triggers lifespan hooks / settings).
from app.main import app  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def _create_user(db, email: str, verified: bool = False) -> User:
    from pwdlib import PasswordHash

    ph = PasswordHash.recommended()
    user = User(
        full_name="Test User",
        email=email,
        password_hash=ph.hash("password123"),
        is_email_verified=verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_token(db, user_id: int, purpose: TokenPurpose) -> str:
    from app.email_tokens.service import create_token

    return create_token(db, user_id=user_id, purpose=purpose)


# ===========================================================================
# Registration
# ===========================================================================

def test_register_creates_email_token(client, db):
    resp = client.post(
        "/users/register",
        json={"full_name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    assert resp.status_code == 201, resp.text

    token = db.query(EmailToken).filter_by(purpose=TokenPurpose.EMAIL_VERIFICATION).first()
    assert token is not None
    assert token.used is False


def test_register_includes_is_email_verified_false(client):
    resp = client.post(
        "/users/register",
        json={"full_name": "Bob", "email": "bob@example.com", "password": "password123"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["is_email_verified"] is False


# ===========================================================================
# Email verification
# ===========================================================================

def test_verify_email_success(client, db):
    user = _create_user(db, "verify@example.com")
    raw = _make_token(db, user.id, TokenPurpose.EMAIL_VERIFICATION)

    resp = client.get(f"/users/verify-email?token={raw}")
    assert resp.status_code == 200, resp.text
    assert "verified" in resp.json()["message"].lower()

    db.refresh(user)
    assert user.is_email_verified is True

    token_row = db.query(EmailToken).filter_by(user_id=user.id).first()
    assert token_row.used is True


def test_verify_email_invalid_token(client):
    resp = client.get("/users/verify-email?token=totallyinvalidtoken")
    assert resp.status_code == 400


def test_verify_email_token_reuse_rejected(client, db):
    user = _create_user(db, "reuse@example.com")
    raw = _make_token(db, user.id, TokenPurpose.EMAIL_VERIFICATION)

    client.get(f"/users/verify-email?token={raw}")         # first use → 200
    resp = client.get(f"/users/verify-email?token={raw}")  # reuse → 400
    assert resp.status_code == 400


def test_verify_email_expired_token_rejected(client, db):
    user = _create_user(db, "expired@example.com")

    raw = "some_raw_token_value"
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expired_record = EmailToken(
        user_id=user.id,
        token_hash=token_hash,
        purpose=TokenPurpose.EMAIL_VERIFICATION,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(expired_record)
    db.commit()

    resp = client.get(f"/users/verify-email?token={raw}")
    assert resp.status_code == 400


# ===========================================================================
# Resend verification
# ===========================================================================

def test_resend_verification_unknown_email_returns_generic(client):
    resp = client.post(
        "/users/resend-verification",
        json={"email": "nobody@example.com"},
    )
    assert resp.status_code == 200  # never reveals whether email exists


def test_resend_verification_already_verified_returns_generic(client, db):
    _create_user(db, "alreadyverified@example.com", verified=True)

    resp = client.post(
        "/users/resend-verification",
        json={"email": "alreadyverified@example.com"},
    )
    assert resp.status_code == 200


def test_resend_verification_invalidates_old_token(client, db):
    user = _create_user(db, "resend@example.com")
    old_raw = _make_token(db, user.id, TokenPurpose.EMAIL_VERIFICATION)

    resp = client.post(
        "/users/resend-verification",
        json={"email": "resend@example.com"},
    )
    assert resp.status_code == 200

    # Old token must now be marked used.
    old_hash = hashlib.sha256(old_raw.encode()).hexdigest()
    db.expire_all()
    old_record = db.query(EmailToken).filter_by(token_hash=old_hash).first()
    assert old_record.used is True

    # A fresh unused token must exist.
    new_record = (
        db.query(EmailToken)
        .filter_by(user_id=user.id, purpose=TokenPurpose.EMAIL_VERIFICATION, used=False)
        .first()
    )
    assert new_record is not None


# ===========================================================================
# Forgot password
# ===========================================================================

def test_forgot_password_unknown_email_returns_generic(client):
    resp = client.post(
        "/users/forgot-password",
        json={"email": "ghost@example.com"},
    )
    assert resp.status_code == 200  # generic; no enumeration


def test_forgot_password_creates_reset_token(client, db):
    _create_user(db, "reset@example.com")

    resp = client.post(
        "/users/forgot-password",
        json={"email": "reset@example.com"},
    )
    assert resp.status_code == 200

    token = db.query(EmailToken).filter_by(purpose=TokenPurpose.PASSWORD_RESET).first()
    assert token is not None


# ===========================================================================
# Reset password
# ===========================================================================

def test_reset_password_success(client, db):
    user = _create_user(db, "changeme@example.com", verified=True)
    raw = _make_token(db, user.id, TokenPurpose.PASSWORD_RESET)

    resp = client.post(
        "/users/reset-password",
        json={"token": raw, "new_password": "newpassword99"},
    )
    assert resp.status_code == 200, resp.text
    assert "successfully" in resp.json()["message"].lower()

    # Token must be consumed.
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    db.expire_all()
    record = db.query(EmailToken).filter_by(token_hash=token_hash).first()
    assert record.used is True

    # Original password must no longer work; new password must work.
    bad_login = client.post(
        "/users/login",
        json={"email": "changeme@example.com", "password": "password123"},
    )
    assert bad_login.status_code == 401

    good_login = client.post(
        "/users/login",
        json={"email": "changeme@example.com", "password": "newpassword99"},
    )
    assert good_login.status_code == 200
    assert "access_token" in good_login.json()


def test_reset_password_invalid_token(client):
    resp = client.post(
        "/users/reset-password",
        json={"token": "badtoken", "new_password": "newpassword99"},
    )
    assert resp.status_code == 400


def test_reset_password_wrong_purpose_rejected(client, db):
    """A verification token MUST NOT be accepted as a password-reset token."""
    user = _create_user(db, "wrongpurpose@example.com")
    raw = _make_token(db, user.id, TokenPurpose.EMAIL_VERIFICATION)

    resp = client.post(
        "/users/reset-password",
        json={"token": raw, "new_password": "newpassword99"},
    )
    assert resp.status_code == 400


def test_reset_password_reuse_rejected(client, db):
    user = _create_user(db, "reuse2@example.com")
    raw = _make_token(db, user.id, TokenPurpose.PASSWORD_RESET)

    client.post(
        "/users/reset-password",
        json={"token": raw, "new_password": "first_new_pass"},
    )
    resp = client.post(
        "/users/reset-password",
        json={"token": raw, "new_password": "second_new_pass"},
    )
    assert resp.status_code == 400
