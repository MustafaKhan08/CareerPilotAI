"""Shared test fixtures for CareerPilotAI test suite.

Uses a single in-memory SQLite database (StaticPool) so all tests
and dependency overrides share the exact same connection.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Register all models with Base.metadata before create_all()
from app.db.database import Base, get_db
from app.users.model import User  # noqa: F401
from app.email_tokens.model import EmailToken  # noqa: F401
from app.resumes.model import Resume  # noqa: F401
from app.analyses.model import ResumeAnalysis  # noqa: F401
from app.interviews.model import (  # noqa: F401
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
)
from app.main import app

SQLITE_URL = "sqlite://"

_ENGINE = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_Session = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)


def _override_get_db():
    session = _Session()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _reset_db():
    """Create all tables before each test; drop them after."""
    Base.metadata.create_all(bind=_ENGINE)
    yield
    Base.metadata.drop_all(bind=_ENGINE)


@pytest.fixture()
def db():
    """Direct DB session sharing the same StaticPool connection."""
    session = _Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    """TestClient with Resend stubbed out."""
    with patch("resend.Emails.send", return_value=MagicMock()):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
