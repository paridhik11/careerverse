"""Alembic environment configuration for CareerVerse AI.

Reuses the app's own settings and SQLAlchemy models instead of a second,
hand-maintained config: `sqlalchemy.url` comes from
`app.core.config.settings.database_url` (falling back to the same local
SQLite file `app.core.database` uses), and `target_metadata` comes from
`app.core.database.Base`, after importing every model module so they're all
registered on it (mirrors the imports in `app.main`).
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.models import job_description as _job_description_model  # noqa: E402,F401
from app.models import job_match as _job_match_model  # noqa: E402,F401
from app.models import job_simulation as _job_simulation_model  # noqa: E402,F401
from app.models import report as _report_model  # noqa: E402,F401
from app.models import resume as _resume_model  # noqa: E402,F401
from app.models import skill_gap as _skill_gap_model  # noqa: E402,F401
from app.models import user as _user_model  # noqa: E402,F401

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# Same fallback as `app.core.database` so `alembic upgrade head` works
# out of the box against a fresh checkout before Postgres is provisioned.
config.set_main_option(
    "sqlalchemy.url", settings.database_url or "sqlite:///./careerverse.sqlite3"
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
