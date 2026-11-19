"""Organization and Member Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.users.schemas import UserRead


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=100)
    avatar_url: Optional[str] = None
    plan: str = "team"  # community, team, enterprise
    max_repos: int = 50


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: Optional[str] = None  # auto-generated if omitted
    avatar_url: Optional[str] = None
    plan: Optional[str] = "team"


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    avatar_url: Optional[str] = None
    plan: Optional[str] = None
    max_repos: Optional[int] = None


class OrganizationRead(OrganizationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationMemberBase(BaseModel):
    role: str = "reviewer"  # admin, maintainer, reviewer, auditor


class OrganizationMemberCreate(OrganizationMemberBase):
    user_id: str


class OrganizationMemberUpdate(BaseModel):
    role: str


class OrganizationMemberRead(OrganizationMemberBase):
    id: str
    organization_id: str
    user_id: str
    user: Optional[UserRead] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
