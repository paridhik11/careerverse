"""SQLAlchemy ORM model for application users."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Nullable: Google-only accounts (see google_id below) never set a local password.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Google's stable per-account identifier (the ID token's `sub` claim). Used
    # to look up Google-authenticated users instead of email, since Google
    # explicitly recommends against using email as a lookup key (it can change).
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
