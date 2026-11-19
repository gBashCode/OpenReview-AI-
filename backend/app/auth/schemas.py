"""Authentication Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """JWT Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until expiration


class TokenPayload(BaseModel):
    """Decoded JWT claims schema."""
    sub: str  # User ID
    exp: int  # Expiration timestamp
    email: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """User credential login schema."""
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """User registration schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: str = Field(..., min_length=8)
    organization_name: Optional[str] = None  # If provided, creates default org for user


class GitHubOAuthURLResponse(BaseModel):
    """GitHub OAuth authorize URL response."""
    url: str


class GitHubOAuthCallbackRequest(BaseModel):
    """Payload to exchange GitHub authorization code."""
    code: str
    redirect_uri: Optional[str] = None
