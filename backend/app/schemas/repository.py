"""Repository schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RepositoryBase(BaseModel):
    owner: str = Field(..., max_length=100, examples=["octocat"])
    name: str = Field(..., max_length=100, examples=["Hello-World"])
    default_branch: str = Field(default="main", max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    clone_url: Optional[str] = None


class RepositoryCreate(RepositoryBase):
    github_repo_id: int = Field(..., examples=[1296269])


class RepositoryUpdate(BaseModel):
    default_branch: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RepositoryRead(RepositoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    github_repo_id: int
    full_name: str
    created_at: datetime
    updated_at: datetime
