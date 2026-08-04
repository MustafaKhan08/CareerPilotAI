"""create interview tables

Revision ID: 77f87de93a4c
Revises: a3d57e91c2b4
Create Date: 2026-08-05 02:35:30.036462

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "77f87de93a4c"
down_revision: Union[str, Sequence[str], None] = "a3d57e91c2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


interview_type = sa.Enum(
    "hr",
    "technical",
    "resume",
    "behavioral",
    "mixed",
    name="interview_type",
)

interview_difficulty = sa.Enum(
    "beginner",
    "intermediate",
    "advanced",
    name="interview_difficulty",
)

interview_status = sa.Enum(
    "pending",
    "in_progress",
    "completed",
    "abandoned",
    name="interview_status",
)


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "interview_sessions",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),

        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "resume_id",
            sa.Integer(),
            sa.ForeignKey(
                "resumes.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "interview_type",
            sa.Enum(
                "hr",
                "technical",
                "resume",
                "behavioral",
                "mixed",
                name="interview_type",
                create_type=False,
            ),
            nullable=False,
        ),

        sa.Column(
            "difficulty",
            sa.Enum(
                "beginner",
                "intermediate",
                "advanced",
                name="interview_difficulty",
                create_type=False,
            ),
            nullable=False,
        ),

        sa.Column(
            "target_role",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "total_questions",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "current_question_number",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "abandoned",
                name="interview_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),

        sa.Column(
            "overall_score",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "summary",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "recommendations",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_interview_sessions_user_id",
        "interview_sessions",
        ["user_id"],
    )

    op.create_index(
        "ix_interview_sessions_resume_id",
        "interview_sessions",
        ["resume_id"],
    )

    op.create_index(
        "ix_interview_sessions_status",
        "interview_sessions",
        ["status"],
    )

    op.create_index(
        "ix_interview_sessions_created_at",
        "interview_sessions",
        ["created_at"],
    )

    op.create_table(
        "interview_questions",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),

        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey(
                "interview_sessions.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "question_order",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "question",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_interview_questions_session_id",
        "interview_questions",
        ["session_id"],
    )

    op.create_index(
        "ix_interview_questions_created_at",
        "interview_questions",
        ["created_at"],
    )

    op.create_unique_constraint(
        "uq_interview_question_order",
        "interview_questions",
        [
            "session_id",
            "question_order",
        ],
    )

    op.create_table(
        "interview_answers",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),

        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey(
                "interview_questions.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            unique=True,
        ),

        sa.Column(
            "answer",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "evaluation",
            sa.JSON(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_interview_answers_created_at",
        "interview_answers",
        ["created_at"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("interview_answers")
    op.drop_table("interview_questions")
    op.drop_table("interview_sessions")