"""Password hashing, JWT, and Google ID token verification helpers."""

from datetime import datetime, timedelta, timezone

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours — fine for an MVP session length

# Falls back to a clearly-labelled dev-only secret so the app still runs before
# JWT_SECRET is configured. Never rely on this fallback in production — set
# JWT_SECRET in the environment (see .env.example).
_JWT_SECRET = settings.jwt_secret or "dev-only-insecure-secret-change-me"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    """Create a signed JWT whose `sub` claim is the user id (as a string)."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, _JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT. Raises `jose.JWTError` if invalid or expired."""
    return jwt.decode(token, _JWT_SECRET, algorithms=[JWT_ALGORITHM])


class GoogleTokenError(Exception):
    """Raised when a "Sign in with Google" ID token fails verification."""


def verify_google_id_token(credential: str) -> dict:
    """Verify a Google Identity Services ID token and return its claims.

    Checks the signature against Google's public keys, plus the issuer,
    expiry, and audience (our OAuth client id) — the credential's claims must
    never be trusted without this. See:
    https://developers.google.com/identity/gsi/web/guides/verify-google-id-token
    """
    if not settings.google_client_id:
        raise GoogleTokenError("Google sign-in is not configured on this server.")

    try:
        claims = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), audience=settings.google_client_id
        )
    except ValueError as exc:
        raise GoogleTokenError("Invalid or expired Google credential.") from exc

    if not claims.get("email_verified", False):
        raise GoogleTokenError("Your Google account's email is not verified.")

    return claims
