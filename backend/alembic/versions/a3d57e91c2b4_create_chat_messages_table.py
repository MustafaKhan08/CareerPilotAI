"""create chat messages table

Revision ID: a3d57e91c2b4
Revises: 026f777805e1
Create Date: 2026-08-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a3d57e91c2b4"
down_revision: Union[str, Sequence[str], None] = "026f777805e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


chat_role = postgresql.ENUM(
    "system",
    "user",
    "assistant",
    name="chat_role",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""

    chat_role.create(
        op.get_bind(),
        checkfirst=True,
    )

    op.create_table(
        "chat_messages",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "role",
            chat_role,
            nullable=False,
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_chat_messages_user_id",
        "chat_messages",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_chat_messages_created_at",
        "chat_messages",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_chat_messages_created_at",
        table_name="chat_messages",
    )

    op.drop_index(
        "ix_chat_messages_user_id",
        table_name="chat_messages",
    )

    op.drop_table("chat_messages")

    chat_role.drop(
        op.get_bind(),
        checkfirst=True,
    )