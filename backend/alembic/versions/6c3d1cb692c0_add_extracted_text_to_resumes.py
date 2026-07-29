"""add extracted_text to resumes

Revision ID: 6c3d1cb692c0
Revises: 93e00c2bfdb2
Create Date: 2026-07-30 00:35:27.699481
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6c3d1cb692c0"
down_revision: Union[str, Sequence[str], None] = "93e00c2bfdb2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Step 1: Add the column as nullable.
    op.add_column(
        "resumes",
        sa.Column("extracted_text", sa.Text(), nullable=True),
    )

    # Step 2: Populate existing rows.
    op.execute(
        """
        UPDATE resumes
        SET extracted_text = 'Legacy resume uploaded before text extraction was implemented.'
        WHERE extracted_text IS NULL
        """
    )

    # Step 3: Make the column required.
    op.alter_column(
        "resumes",
        "extracted_text",
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("resumes", "extracted_text")