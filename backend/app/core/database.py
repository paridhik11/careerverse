"""SQLAlchemy engine, session factory, and declarative base.

MVP note: tables are created directly from the ORM metadata (see
`Base.metadata.create_all` in `app.main`) instead of via Alembic migrations.
This is fine while the schema is still small and changing quickly; switch to
Alembic-managed migrations (already listed in the tech stack) once the schema
stabilizes and multiple environments need controlled, versioned upgrades.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Falls back to a local SQLite file when DATABASE_URL isn't configured yet (e.g.
# a fresh checkout before Postgres is provisioned). Production deployments must
# set DATABASE_URL to a real Postgres connection string, per .env.example.
_DATABASE_URL = settings.database_url or "sqlite:///./careerverse.sqlite3"

# SQLite needs this flag because FastAPI can hand the same connection to
# different threads; Postgres doesn't need (or accept) this argument.
_connect_args = {"check_same_thread": False} if _DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(_DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for every SQLAlchemy ORM model."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
