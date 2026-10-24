"""add_interview_timer_columns

Adds duration_minutes and deadline_at to interview_sessions,
and adds 'timed_out' to the interview_status enum.

Revision ID: a1b2c3d4e5f6
Revises: 2cc7d50cfb53
Create Date: 2026-10-24 22:42:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2cc7d50cfb53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Add 'timed_out' to the interview_status PostgreSQL enum.
    #    ALTER TYPE ... ADD VALUE is idempotent in Postgres 9.6+ via
    #    IF NOT EXISTS (Postgres 14+). For non-Postgres engines (e.g. SQLite),
    #    this is safely skipped.
    # ------------------------------------------------------------------
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TYPE interview_status ADD VALUE IF NOT EXISTS 'timed_out'"
        )

    # ------------------------------------------------------------------
    # 2. Add duration_minutes column (integer, not null, default 15).
    #    Existing rows get the default of 15.
    # ------------------------------------------------------------------
    op.add_column(
        "interview_sessions",
        sa.Column(
            "duration_minutes",
            sa.Integer(),
            nullable=False,
            server_default="15",
        ),
    )

    # ------------------------------------------------------------------
    # 3. Add deadline_at column (timezone-aware timestamp, nullable).
    #    Existing rows will have NULL — the backend treats NULL as
    #    "no deadline" and will not enforce a cutoff for legacy sessions.
    # ------------------------------------------------------------------
    op.add_column(
        "interview_sessions",
        sa.Column(
            "deadline_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # Remove the two new columns.
    # Note: removing an enum value from a PostgreSQL enum requires
    # recreating the type; we do NOT downgrade the enum value to keep
    # the downgrade safe and reversible.
    op.drop_column("interview_sessions", "deadline_at")
    op.drop_column("interview_sessions", "duration_minutes")
