"""FastAPI dependency injection providers."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.services.auth_service import get_user_by_id

# `tokenUrl` only documents where a token can be obtained (used by /docs); the
# frontend sends the JWT as `Authorization: Bearer <token>` on every request.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a bearer JWT, or raise 401."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_error

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except JWTError as exc:
        raise credentials_error from exc

    if user_id is None:
        raise credentials_error

    user = get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_error

    return user
