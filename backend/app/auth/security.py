"""Password verification and JWT utilities."""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.users.model import User

password_hasher = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a plain-text password against its hashed value."""

    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    data: dict[str, Any],
) -> str:
    """Create a signed JWT access token."""

    token_data = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    token_data.update(
        {
            "exp": expire,
        }
    )

    return jwt.encode(
        token_data,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Decode a bearer token and return the authenticated user."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (JWTError, TypeError, ValueError):
        raise credentials_exception

    from app.users.service import get_user_by_id

    user = get_user_by_id(db, user_id)

    if user is None:
        raise credentials_exception

    return user