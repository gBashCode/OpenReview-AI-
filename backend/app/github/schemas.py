"""GitHub Integration Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class GitHubInstallationBase(BaseModel):
    installation_id: int
    account_login: str
    account_type: str = "Organization"  # User, Organization
    permissions_json: Optional[str] = None


class GitHubInstallationCreate(GitHubInstallationBase):
    organization_id: str


class GitHubInstallationRead(GitHubInstallationBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GitHubRepositoryItem(BaseModel):
    """Schema for repository item returned by GitHub API."""
    id: int
    name: str
    full_name: str
    private: bool
    description: Optional[str] = None
    default_branch: str = "main"
    clone_url: Optional[str] = None
    html_url: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None


class GitHubInstallationReposResponse(BaseModel):
    total_count: int
    repositories: List[GitHubRepositoryItem]


class GitHubChangedFile(BaseModel):
    """Schema for individual changed files in a pull request."""
    sha: str
    filename: str
    status: str  # modified, added, removed, renamed
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None
    raw_url: Optional[str] = None


class GitHubInlineComment(BaseModel):
    """Inline review comment schema to be posted to GitHub PR."""
    path: str
    line: int
    side: Literal["LEFT", "RIGHT"] = "RIGHT"
    body: str


class GitHubReviewCreate(BaseModel):
    """Batch review submission schema to GitHub API."""
    commit_id: str
    body: str
    event: Literal["COMMENT", "APPROVE", "REQUEST_CHANGES"] = "COMMENT"
    comments: Optional[List[GitHubInlineComment]] = None


class GitHubCheckRunAnnotation(BaseModel):
    path: str
    start_line: int
    end_line: int
    annotation_level: Literal["notice", "warning", "failure"]
    message: str
    title: Optional[str] = None
    raw_details: Optional[str] = None


class GitHubCheckRunOutput(BaseModel):
    title: str
    summary: str
    text: Optional[str] = None
    annotations: Optional[List[GitHubCheckRunAnnotation]] = None


class GitHubCheckRunCreate(BaseModel):
    name: str = "OpenReview AI / Multi-Agent Code Review"
    head_sha: str
    status: Literal["queued", "in_progress", "completed"] = "queued"
    conclusion: Optional[Literal["action_required", "cancelled", "failure", "neutral", "success", "skipped", "timed_out"]] = None
    output: Optional[GitHubCheckRunOutput] = None
