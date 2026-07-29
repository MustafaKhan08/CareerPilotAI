"""update resume metadata

Revision ID: 93e00c2bfdb2
Revises: 0a6e734bff93
Create Date: 2026-07-29 23:09:17.021254

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "93e00c2bfdb2"
down_revision: Union[str, Sequence[str], None] = "0a6e734bff93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Remove the legacy title column.
    op.drop_column("resumes", "title")

    # Rename file_name -> original_filename while preserving existing data.
    op.alter_column(
        "resumes",
        "file_name",
        new_column_name="original_filename",
    )

    # Add stored_filename as nullable first.
    op.add_column(
        "resumes",
        sa.Column(
            "stored_filename",
            sa.String(length=255),
            nullable=True,
        ),
    )

    # Populate existing rows.
    op.execute(
        """
        UPDATE resumes
        SET stored_filename = original_filename
        WHERE stored_filename IS NULL
        """
    )

    # Make the column required.
    op.alter_column(
        "resumes",
        "stored_filename",
        nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Allow NULL before dropping.
    op.alter_column(
        "resumes",
        "stored_filename",
        nullable=True,
    )

    # Remove stored_filename.
    op.drop_column(
        "resumes",
        "stored_filename",
    )

    # Rename original_filename back to file_name.
    op.alter_column(
        "resumes",
        "original_filename",
        new_column_name="file_name",
    )

    # Restore title column.
    op.add_column(
        "resumes",
        sa.Column(
            "title",
            sa.String(length=255),
            server_default=sa.text("''"),
            nullable=False,
        ),
    )