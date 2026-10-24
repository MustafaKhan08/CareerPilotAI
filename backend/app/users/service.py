"""User registration and authentication business logic."""

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.security import verify_password
from app.users.model import User
from app.users.schema import UserCreate

password_hasher = PasswordHash.recommended()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Return the user matching an email address."""

    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Return the user matching a primary-key identifier."""

    return db.get(User, user_id)


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create and persist a new user."""

    if get_user_by_email(db, user_data.email):
        raise ValueError("Email already registered")

    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        password_hash=password_hasher.hash(user_data.password),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Email already registered")

    db.refresh(user)

    return user




def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    """Authenticate credentials and require a verified, active account."""

    user = get_user_by_email(db, email)

    if user is None:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if not user.is_email_verified:
        raise ValueError(
            "Please verify your email address before signing in."
        )

    if not user.is_active:
        raise ValueError(
            "Your account is inactive. Please contact support."
        )

    return user
