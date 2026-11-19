"""Repository Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RepositoryBase(BaseModel):
    owner: str = Field(..., max_length=100)
    name: str = Field(..., max_length=100)
    default_branch: str = "main"
    description: Optional[str] = None
    is_active: bool = True
    clone_url: Optional[str] = None


class RepositoryCreate(BaseModel):
    owner: str
    name: str
    organization_id: Optional[str] = None
    github_repo_id: Optional[int] = None
    default_branch: Optional[str] = "main"
    description: Optional[str] = None
    is_active: Optional[bool] = True
    clone_url: Optional[str] = None


class RepositoryUpdate(BaseModel):
    default_branch: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RepositoryRead(RepositoryBase):
    id: str
    organization_id: str
    github_repo_id: int
    full_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
