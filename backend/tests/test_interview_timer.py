"""Tests for Interview Timer, Timeout Finalization, and Partial Reports.

Uses an in-memory SQLite database (StaticPool) and mocks AI calls.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pydantic
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.users.model import User
from app.resumes.model import Resume
from app.analyses.model import ResumeAnalysis
from app.interviews.model import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    InterviewStatus,
    InterviewType,
    InterviewDifficulty,
)
from app.interviews.schema import (
    InterviewStartRequest,
    InterviewSessionStartResponse,
    InterviewReportResponse,
    InterviewTimeoutResponse,
    InterviewEvaluationResponse,
)
from app.interviews.service import (
    finalize_timeout,
    get_or_generate_report,
    get_report_pdf,
    submit_answer,
    _build_interview_transcript,
)
from app.main import app


@pytest.fixture()
def test_user(db):
    user = User(
        full_name="Candidate Bob",
        email="candidate.bob@example.com",
        password_hash="fakehash",
        is_email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def test_resume(db, test_user):
    resume = Resume(
        user_id=test_user.id,
        original_filename="test_resume.pdf",
        stored_filename="test_resume_stored.pdf",
        file_path="/tmp/test_resume.pdf",
        file_type="application/pdf",
        extracted_text="Experienced Software Engineer with Python and React.",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


# ===========================================================================
# 1. Validation & Schema Tests
# ===========================================================================

def test_duration_minutes_validation():
    """Duration must be a whole number between 1 and 60 minutes."""
    # Valid
    r1 = InterviewStartRequest(
        title="Valid 1", target_role="Engineer",
        interview_type=InterviewType.HR, difficulty=InterviewDifficulty.BEGINNER,
        duration_minutes=1
    )
    assert r1.duration_minutes == 1

    r15 = InterviewStartRequest(
        title="Valid 15", target_role="Engineer",
        interview_type=InterviewType.HR, difficulty=InterviewDifficulty.BEGINNER,
        duration_minutes=15
    )
    assert r15.duration_minutes == 15

    r60 = InterviewStartRequest(
        title="Valid 60", target_role="Engineer",
        interview_type=InterviewType.HR, difficulty=InterviewDifficulty.BEGINNER,
        duration_minutes=60
    )
    assert r60.duration_minutes == 60

    # Invalid: 0, negative, > 60
    for invalid_duration in [0, -1, -10, 61, 100]:
        with pytest.raises(pydantic.ValidationError):
            InterviewStartRequest(
                title="Bad", target_role="Engineer",
                interview_type=InterviewType.HR, difficulty=InterviewDifficulty.BEGINNER,
                duration_minutes=invalid_duration
            )


def test_schema_fields_present():
    """Ensure deadline_at, is_partial, status, and timeout schemas are present."""
    assert "deadline_at" in InterviewSessionStartResponse.model_fields
    assert "is_partial" in InterviewReportResponse.model_fields
    assert "status" in InterviewReportResponse.model_fields
    assert hasattr(InterviewStatus, "TIMED_OUT")


# ===========================================================================
# 2. Server-side Deadline Enforcement Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_late_answer_rejected(db, test_user, test_resume):
    """Answers submitted after deadline_at must be rejected with 409 Conflict."""
    from fastapi import HTTPException

    # Create session with deadline in the past
    past_deadline = datetime.now(timezone.utc) - timedelta(minutes=5)
    session = InterviewSession(
        user_id=test_user.id,
        resume_id=test_resume.id,
        title="Late Test",
        interview_type=InterviewType.TECHNICAL,
        difficulty=InterviewDifficulty.INTERMEDIATE,
        target_role="Backend Dev",
        total_questions=5,
        current_question_number=1,
        status=InterviewStatus.IN_PROGRESS,
        duration_minutes=15,
        deadline_at=past_deadline,
        started_at=datetime.now(timezone.utc) - timedelta(minutes=20),
    )
    db.add(session)
    db.flush()

    question = InterviewQuestion(
        session_id=session.id,
        question_order=1,
        question="What is dependency injection?",
    )
    db.add(question)
    db.commit()

    # Attempt to submit an answer after deadline
    with pytest.raises(HTTPException) as exc_info:
        await submit_answer(
            db=db,
            current_user=test_user,
            session_id=session.id,
            candidate_answer="Dependency injection is a design pattern...",
        )

    assert exc_info.value.status_code == 409
    assert "expired" in exc_info.value.detail.lower()


# ===========================================================================
# 3. Timeout Finalization & Zero-Answer Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_zero_answer_timeout_generates_honest_report(db, test_user, test_resume):
    """When an interview times out with 0 answers, generate an honest report without fabricated scores."""
    session = InterviewSession(
        user_id=test_user.id,
        resume_id=test_resume.id,
        title="Zero Answer Test",
        interview_type=InterviewType.TECHNICAL,
        difficulty=InterviewDifficulty.INTERMEDIATE,
        target_role="Backend Dev",
        total_questions=5,
        current_question_number=1,
        status=InterviewStatus.IN_PROGRESS,
        duration_minutes=15,
        deadline_at=datetime.now(timezone.utc) - timedelta(seconds=10),
        started_at=datetime.now(timezone.utc) - timedelta(minutes=15),
    )
    db.add(session)
    db.flush()

    question = InterviewQuestion(
        session_id=session.id,
        question_order=1,
        question="Explain polymorphism in Python.",
    )
    db.add(question)
    db.commit()

    # Finalize timeout
    resp = await finalize_timeout(
        db=db,
        current_user=test_user,
        session_id=session.id,
    )

    assert isinstance(resp, InterviewTimeoutResponse)
    assert resp.session_id == session.id

    db.refresh(session)
    assert session.status == InterviewStatus.TIMED_OUT
    assert session.overall_score == 0.0
    assert "no answers" in session.summary.lower() or "ended before" in session.summary.lower()

    # Verify report endpoint serves this timed-out session
    report = await get_or_generate_report(
        db=db,
        current_user=test_user,
        session_id=session.id,
    )
    assert report.is_partial is True
    assert report.status == InterviewStatus.TIMED_OUT
    assert report.overall_score == 0.0

    # Verify PDF generation succeeds for zero-answer timed-out session
    pdf_bytes = get_report_pdf(
        db=db,
        current_user=test_user,
        session_id=session.id,
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


@pytest.mark.asyncio
async def test_finalize_timeout_is_idempotent(db, test_user, test_resume):
    """Calling finalize_timeout repeatedly on an already-finalized session returns success without re-running."""
    session = InterviewSession(
        user_id=test_user.id,
        resume_id=test_resume.id,
        title="Idempotent Test",
        interview_type=InterviewType.TECHNICAL,
        difficulty=InterviewDifficulty.BEGINNER,
        target_role="Developer",
        total_questions=3,
        current_question_number=1,
        status=InterviewStatus.IN_PROGRESS,
        duration_minutes=10,
        deadline_at=datetime.now(timezone.utc) - timedelta(seconds=5),
    )
    db.add(session)
    db.commit()

    # First call
    resp1 = await finalize_timeout(db=db, current_user=test_user, session_id=session.id)
    assert resp1.session_id == session.id

    # Second call (idempotent)
    resp2 = await finalize_timeout(db=db, current_user=test_user, session_id=session.id)
    assert resp2.session_id == session.id
    assert "already finalized" in resp2.message.lower()


# ===========================================================================
# 4. Partial Report & Transcript Filtering Tests
# ===========================================================================

def test_transcript_excludes_unanswered_questions(db, test_user, test_resume):
    """_build_interview_transcript with only_answered=True must omit unanswered questions."""
    session = InterviewSession(
        user_id=test_user.id,
        resume_id=test_resume.id,
        title="Transcript Filter Test",
        interview_type=InterviewType.HR,
        difficulty=InterviewDifficulty.BEGINNER,
        target_role="Product Manager",
        total_questions=3,
        current_question_number=2,
        status=InterviewStatus.IN_PROGRESS,
        duration_minutes=15,
    )
    db.add(session)
    db.flush()

    q1 = InterviewQuestion(session_id=session.id, question_order=1, question="Tell me about yourself.")
    q2 = InterviewQuestion(session_id=session.id, question_order=2, question="Why do you want this job?")
    db.add_all([q1, q2])
    db.flush()

    ans1 = InterviewAnswer(
        question_id=q1.id,
        answer="I have 5 years of PM experience.",
        evaluation={"score": 8.5, "strengths": ["Clear"], "weaknesses": []},
    )
    db.add(ans1)
    db.commit()
    db.refresh(session)

    # Transcript with only_answered=True
    t_partial = _build_interview_transcript(session, only_answered=True)
    assert "Tell me about yourself" in t_partial
    assert "Why do you want this job" not in t_partial
    assert "[Not answered]" not in t_partial

    # Transcript with only_answered=False includes question 2 as [Not answered]
    t_full = _build_interview_transcript(session, only_answered=False)
    assert "Why do you want this job" in t_full
    assert "[Not answered]" in t_full


# ===========================================================================
# 5. Answer Submission Lifecycle & Timeout Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_submit_answer_completes_as_timed_out_if_deadline_passes_during_eval(db, test_user, test_resume):
    """If AI evaluation finishes after the deadline, session transitions to TIMED_OUT without generating next question."""
    # Start with a deadline that is just 1 second in the future (or already passed by mock time)
    session = InterviewSession(
        user_id=test_user.id,
        resume_id=test_resume.id,
        title="Eval Timeout Test",
        interview_type=InterviewType.HR,
        difficulty=InterviewDifficulty.BEGINNER,
        target_role="Frontend Engineer",
        total_questions=5,
        current_question_number=1,
        status=InterviewStatus.IN_PROGRESS,
        duration_minutes=15,
        deadline_at=datetime.now(timezone.utc) + timedelta(seconds=1),
        started_at=datetime.now(timezone.utc) - timedelta(minutes=14),
    )
    db.add(session)
    db.flush()

    q1 = InterviewQuestion(session_id=session.id, question_order=1, question="What is CSS Flexbox?")
    db.add(q1)
    db.commit()

    # Resume analysis mock context
    analysis = ResumeAnalysis(
        resume_id=test_resume.id,
        provider="nvidia",
        model_name="nvidia/nemotron-3-ultra-550b-a55b",
        ats_score=85,
        career_domain="Frontend Engineering",
        experience_level="Mid",
        summary="Good resume",
        skills=["CSS", "HTML", "JS"],
        missing_skills=[],
        strengths=["Layouts"],
        weaknesses=[],
        suggestions=["Practice"],
    )
    db.add(analysis)
    db.commit()

    eval_json = json.dumps({
        "score": 8.0,
        "strengths": ["Clear explanation"],
        "weaknesses": [],
        "communication": "Strong",
        "confidence": "High",
        "technical_accuracy": "Accurate",
        "ideal_answer": "Flexbox is a one-dimensional layout model.",
        "improvements": [],
    })

    report_json = json.dumps({
        "overall_score": 8.0,
        "summary": "Solid partial performance.",
        "strengths": ["CSS Knowledge"],
        "weaknesses": [],
        "recommendations": "Keep going.",
        "career_readiness": "Ready for junior/mid roles.",
        "next_steps": ["Apply"],
    })

    async def mock_generate_chat_response(messages):
        # By the time AI returns, simulate that deadline has expired
        session.deadline_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        db.commit()

        content = messages[-1]["content"]
        if "Evaluate the candidate's answer" in content:
            return eval_json
        return report_json

    with patch("app.interviews.service.generate_chat_response", side_effect=mock_generate_chat_response):
        resp = await submit_answer(
            db=db,
            current_user=test_user,
            session_id=session.id,
            candidate_answer="Flexbox is a one-dimensional CSS layout model.",
        )

    # Must complete interview without next question
    assert resp.completed is True
    assert resp.next_question is None
    assert resp.score == 8.0

    db.refresh(session)
    assert session.status == InterviewStatus.TIMED_OUT
    assert session.completed_at is not None

    # Verify report is marked as partial
    report = await get_or_generate_report(db=db, current_user=test_user, session_id=session.id)
    assert report.is_partial is True
    assert report.status == InterviewStatus.TIMED_OUT
    assert report.overall_score == 8.0


@pytest.mark.asyncio
async def test_submit_answer_normal_completion_before_deadline(db, test_user, test_resume):
    """Answering the final question before deadline completes normally with status COMPLETED and is_partial=False."""
    session = InterviewSession(
        user_id=test_user.id,
        resume_id=test_resume.id,
        title="Normal Complete Test",
        interview_type=InterviewType.TECHNICAL,
        difficulty=InterviewDifficulty.INTERMEDIATE,
        target_role="Fullstack Developer",
        total_questions=1,  # 1 total question -> answering it is the final question
        current_question_number=1,
        status=InterviewStatus.IN_PROGRESS,
        duration_minutes=30,
        deadline_at=datetime.now(timezone.utc) + timedelta(minutes=25),
        started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    db.add(session)
    db.flush()

    q1 = InterviewQuestion(session_id=session.id, question_order=1, question="Explain REST vs GraphQL.")
    db.add(q1)
    db.commit()

    analysis = ResumeAnalysis(
        resume_id=test_resume.id,
        provider="nvidia",
        model_name="nvidia/nemotron-3-ultra-550b-a55b",
        ats_score=90,
        career_domain="Fullstack Engineering",
        experience_level="Senior",
        summary="Strong profile",
        skills=["API", "REST"],
        missing_skills=[],
        strengths=["Deep understanding"],
        weaknesses=[],
        suggestions=[],
    )
    db.add(analysis)
    db.commit()

    eval_json = json.dumps({
        "score": 9.0,
        "strengths": ["Deep understanding"],
        "weaknesses": [],
        "communication": "Clear",
        "confidence": "High",
        "technical_accuracy": "Precise",
        "ideal_answer": "REST uses standard HTTP methods, GraphQL uses single endpoint query language.",
        "improvements": [],
    })

    report_json = json.dumps({
        "overall_score": 9.0,
        "summary": "Excellent complete interview.",
        "strengths": ["REST expertise"],
        "weaknesses": [],
        "recommendations": "Ready for production.",
        "career_readiness": "Fully ready.",
        "next_steps": ["Offer candidate"],
    })

    async def mock_generate_chat_response(messages):
        content = messages[-1]["content"]
        if "Evaluate the candidate's answer" in content:
            return eval_json
        return report_json

    with patch("app.interviews.service.generate_chat_response", side_effect=mock_generate_chat_response):
        resp = await submit_answer(
            db=db,
            current_user=test_user,
            session_id=session.id,
            candidate_answer="REST uses multiple endpoints and standard HTTP verbs, while GraphQL uses a schema and query language over a single endpoint.",
        )

    assert resp.completed is True
    assert resp.next_question is None

    db.refresh(session)
    assert session.status == InterviewStatus.COMPLETED

    report = await get_or_generate_report(db=db, current_user=test_user, session_id=session.id)
    assert report.is_partial is False
    assert report.status == InterviewStatus.COMPLETED
    assert report.overall_score == 9.0
