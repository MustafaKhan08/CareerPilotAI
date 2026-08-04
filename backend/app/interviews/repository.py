"""Repository layer for the Interview Preparation module."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.interviews.model import (
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
)
from app.users.model import User


# ==========================================================
# SESSION
# ==========================================================


def create_interview_session(
    db: Session,
    session: InterviewSession,
) -> InterviewSession:
    """
    Persist a new interview session.

    The caller is responsible for committing.
    """

    db.add(session)
    db.flush()
    db.refresh(session)

    return session


def get_interview_session(
    db: Session,
    session_id: int,
    current_user: User,
) -> InterviewSession | None:
    """
    Return an interview session owned by the user.
    """

    statement = (
        select(InterviewSession)
        .where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
        .options(
            joinedload(
                InterviewSession.questions
            ).joinedload(
                InterviewQuestion.answer
            )
        )
    )

    return db.scalar(statement)


def get_interview_history(
    db: Session,
    current_user: User,
) -> list[InterviewSession]:
    """
    Return every interview session for a user.
    """

    statement = (
        select(InterviewSession)
        .where(
            InterviewSession.user_id == current_user.id,
        )
        .order_by(
            InterviewSession.created_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )


def delete_interview_session(
    db: Session,
    session: InterviewSession,
) -> None:
    """
    Delete an interview session.

    The caller commits the transaction.
    """

    db.delete(session)
    db.flush()


# ==========================================================
# QUESTIONS
# ==========================================================


def create_question(
    db: Session,
    question: InterviewQuestion,
) -> InterviewQuestion:
    """
    Persist a generated question.
    """

    db.add(question)
    db.flush()
    db.refresh(question)

    return question


def get_question(
    db: Session,
    question_id: int,
) -> InterviewQuestion | None:
    """
    Retrieve one interview question.
    """

    statement = select(
        InterviewQuestion
    ).where(
        InterviewQuestion.id == question_id,
    )

    return db.scalar(statement)


def get_session_questions(
    db: Session,
    session_id: int,
) -> list[InterviewQuestion]:
    """
    Return every question in order.
    """

    statement = (
        select(InterviewQuestion)
        .where(
            InterviewQuestion.session_id
            == session_id
        )
        .order_by(
            InterviewQuestion.question_order
        )
    )

    return list(
        db.scalars(statement).all()
    )


def get_latest_question(
    db: Session,
    session_id: int,
) -> InterviewQuestion | None:
    """
    Return the most recently generated
    question for a session.
    """

    statement = (
        select(InterviewQuestion)
        .where(
            InterviewQuestion.session_id == session_id,
        )
        .order_by(
            InterviewQuestion.question_order.desc(),
        )
    )

    return db.scalar(statement)


# ==========================================================
# ANSWERS
# ==========================================================


def create_answer(
    db: Session,
    answer: InterviewAnswer,
) -> InterviewAnswer:
    """
    Persist a user answer.
    """

    db.add(answer)
    db.flush()
    db.refresh(answer)

    return answer


def get_answer(
    db: Session,
    question_id: int,
) -> InterviewAnswer | None:
    """
    Return the answer for a question.
    """

    statement = select(
        InterviewAnswer
    ).where(
        InterviewAnswer.question_id
        == question_id,
    )

    return db.scalar(statement)


# ==========================================================
# UPDATE
# ==========================================================


def update_session(
    db: Session,
    session: InterviewSession,
) -> InterviewSession:
    """
    Flush updated session fields.

    Commit is handled by the service layer.
    """

    db.add(session)
    db.flush()
    db.refresh(session)

    return session


def update_answer(
    db: Session,
    answer: InterviewAnswer,
) -> InterviewAnswer:
    """
    Flush updated answer fields.

    Commit is handled by the service layer.
    """

    db.add(answer)
    db.flush()
    db.refresh(answer)

    return answer