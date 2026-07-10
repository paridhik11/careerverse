"""Business logic for user signup, login, and lookup.

Raises domain-specific exceptions instead of HTTP errors so this module stays
usable outside of an HTTP context; `app.api.auth` translates these into the
correct status codes.
"""

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_google_id_token,
    verify_password,
)
from app.models.auth import LoginRequest, SignupRequest
from app.models.user import User


class EmailAlreadyRegisteredError(Exception):
    """Raised on signup when the email is already tied to an account."""


class InvalidCredentialsError(Exception):
    """Raised on login when the email/password combination doesn't match."""


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def signup(db: Session, payload: SignupRequest) -> tuple[User, str]:
    """Create a new user account. Returns the user and a fresh access token."""
    if get_user_by_email(db, payload.email) is not None:
        raise EmailAlreadyRegisteredError(
            f"An account with email '{payload.email}' already exists."
        )

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return user, token


def login(db: Session, payload: LoginRequest) -> tuple[User, str]:
    """Authenticate a user. Returns the user and a fresh access token."""
    user = get_user_by_email(db, payload.email)
    # `user.hashed_password` is None for Google-only accounts — same generic
    # error either way, so we don't leak which accounts exist or how they
    # authenticate.
    if (
        user is None
        or user.hashed_password is None
        or not verify_password(payload.password, user.hashed_password)
    ):
        raise InvalidCredentialsError("Incorrect email or password.")

    token = create_access_token(subject=str(user.id))
    return user, token


def authenticate_with_google(db: Session, credential: str) -> tuple[User, str]:
    """Find or create a user from a verified Google ID token.

    Raises `app.core.security.GoogleTokenError` if the credential itself is
    invalid — that's left to bubble up so the route can turn it into a 401.
    """
    claims = verify_google_id_token(credential)
    google_id = str(claims["sub"])
    email = str(claims["email"])

    user = db.query(User).filter(User.google_id == google_id).first()

    if user is None:
        # No account tied to this Google id yet — link an existing
        # password account with the same (Google-verified) email, or
        # create a brand new Google-only account.
        user = get_user_by_email(db, email)
        if user is not None:
            user.google_id = google_id
        else:
            user = User(email=email, google_id=google_id, hashed_password=None)
            db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return user, token
