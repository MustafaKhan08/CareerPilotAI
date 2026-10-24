"""Secure token generation and validation for email flows."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.email_tokens.model import EmailToken, TokenPurpose

# ---------------------------------------------------------------------------
# Expiry windows
# ---------------------------------------------------------------------------
VERIFICATION_TOKEN_TTL_HOURS = 24
RESET_TOKEN_TTL_HOURS = 1


def _hash_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest of *raw_token*."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def create_token(
    db: Session,
    *,
    user_id: int,
    purpose: TokenPurpose,
) -> str:
    """Generate a cryptographically secure token, persist its hash, and return
    the raw (unhashed) value that must be sent to the user.

    Any previous unused tokens for the same user + purpose are invalidated
    so only one token per purpose is active at a time.
    """
    # Invalidate existing tokens for this user + purpose.
    from sqlalchemy import select, update

    db.execute(
        update(EmailToken)
        .where(
            EmailToken.user_id == user_id,
            EmailToken.purpose == purpose,
            EmailToken.used == False,  # noqa: E712
        )
        .values(used=True)
    )

    ttl_hours = (
        VERIFICATION_TOKEN_TTL_HOURS
        if purpose == TokenPurpose.EMAIL_VERIFICATION
        else RESET_TOKEN_TTL_HOURS
    )

    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

    record = EmailToken(
        user_id=user_id,
        token_hash=_hash_token(raw_token),
        purpose=purpose,
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()

    return raw_token


def consume_token(
    db: Session,
    *,
    raw_token: str,
    purpose: TokenPurpose,
) -> EmailToken | None:
    """Look up a token by hash, validate expiry and purpose, mark it used.

    Returns the ``EmailToken`` record on success; ``None`` on any failure.
    The caller must never distinguish *which* validation step failed to the
    client (prevents oracle attacks).
    """
    from sqlalchemy import select

    token_hash = _hash_token(raw_token)

    record = db.scalar(
        select(EmailToken).where(
            EmailToken.token_hash == token_hash,
            EmailToken.purpose == purpose,
        )
    )

    if record is None:
        return None

    if record.used:
        return None

    if datetime.now(timezone.utc) > record.expires_at.replace(tzinfo=timezone.utc):
        return None

    record.used = True
    db.commit()

    return record
