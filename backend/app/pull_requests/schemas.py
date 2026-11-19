"""Pull Request Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PullRequestBase(BaseModel):
    repository_id: str
    number: int
    title: str = Field(..., min_length=1, max_length=500)
    source_branch: str
    target_branch: str
    head_sha: str
    base_sha: str
    state: str = "open"  # open, closed, merged
    author_username: Optional[str] = None
    author_avatar_url: Optional[str] = None
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0


class PullRequestCreate(PullRequestBase):
    pass


class PullRequestUpdate(BaseModel):
    title: Optional[str] = None
    state: Optional[str] = None
    head_sha: Optional[str] = None
    base_sha: Optional[str] = None
    additions: Optional[int] = None
    deletions: Optional[int] = None
    changed_files: Optional[int] = None


class PullRequestRead(PullRequestBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
