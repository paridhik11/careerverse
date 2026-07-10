"""Auth route handlers: signup, login, Google sign-in, and the current-user lookup.

Routes only validate the request/response shape and translate service-layer
exceptions into HTTP responses — the actual signup/login logic lives in
`app.services.auth_service`.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import GoogleTokenError
from app.models.auth import (
    GoogleAuthRequest,
    LoginRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.models.user import User
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user, token = auth_service.signup(db, payload)
    except auth_service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user, token = auth_service.login(db, payload)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/auth/google", response_model=TokenResponse)
async def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        user, token = auth_service.authenticate_with_google(db, payload.credential)
    except GoogleTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
