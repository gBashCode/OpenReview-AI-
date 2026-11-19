"""Pull Request schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PullRequestBase(BaseModel):
    pr_number: int = Field(..., examples=[42])
    title: str = Field(..., max_length=255, examples=["feat: add autonomous multi-agent reviewer"])
    description: Optional[str] = None
    head_branch: str = Field(..., max_length=100)
    base_branch: str = Field(..., max_length=100)
    head_sha: str = Field(..., max_length=40)
    base_sha: str = Field(..., max_length=40)
    author_username: str = Field(..., max_length=100)
    state: str = Field(default="open")


class PullRequestCreate(PullRequestBase):
    repository_id: str
    github_pr_id: Optional[int] = None


class PullRequestRead(PullRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    github_pr_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
