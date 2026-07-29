"""Alembic migration environment for CareerPilotAI."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.db.database import Base
from app.users.model import User
from app.resumes.model import Resume
  # Required for Alembic to discover the User model

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load the database URL from the application's settings.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Metadata used by Alembic to discover SQLAlchemy models.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL migration scripts without connecting to the database."""

    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a temporary database connection."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()