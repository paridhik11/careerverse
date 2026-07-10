"""Pydantic request/response schemas for the auth endpoints."""

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

MIN_PASSWORD_LENGTH = 8


class SignupRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        if len(value) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    # The signed JWT ID token returned by Google Identity Services on the
    # frontend (the `credential` field of `CredentialResponse`).
    credential: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
