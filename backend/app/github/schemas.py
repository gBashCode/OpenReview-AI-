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


class GitHubPublishRequest(BaseModel):
    """Request to publish a verified code review to GitHub PR."""
    review_id: str = Field(description="Internal Review UUID")
    owner: Optional[str] = Field(default=None, description="GitHub repository owner/org")
    repo: Optional[str] = Field(default=None, description="GitHub repository name")
    pull_number: Optional[int] = Field(default=None, description="GitHub PR number")
    installation_id: Optional[int] = Field(default=None, description="GitHub App installation ID")
    token: Optional[str] = Field(default=None, description="Optional GitHub Personal Access Token or OAuth token")
    min_actionability: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum actionability score to publish")
    force_comment_event: Optional[Literal["COMMENT", "APPROVE", "REQUEST_CHANGES"]] = Field(
        default=None,
        description="Override automatic review event status"
    )
    manage_outdated: bool = Field(default=True, description="Whether to resolve or reply to outdated comments")


class GitHubPublishResult(BaseModel):
    """Confirmed result of review publishing to GitHub API."""
    status: Literal["published", "partial", "failed"] = Field(description="Overall publish status")
    review_id: str = Field(description="Internal Review UUID")
    github_review_id: Optional[int] = Field(default=None, description="GitHub PR Review ID")
    github_review_url: Optional[str] = Field(default=None, description="HTML URL of GitHub Review")
    check_run_id: Optional[int] = Field(default=None, description="GitHub Check Run ID")
    total_findings: int = 0
    actionable_findings: int = 0
    inline_comments_published: int = 0
    summary_findings_count: int = 0
    duplicate_comments_skipped: int = 0
    outdated_comments_resolved: int = 0
    comment_ids: List[int] = Field(default_factory=list, description="IDs of published inline comments")
    published_at: datetime = Field(default_factory=lambda: datetime.now())
    event: str = Field(default="COMMENT", description="Submitted GitHub Review event (APPROVE/REQUEST_CHANGES/COMMENT)")
    api_confirmed: bool = Field(default=False, description="Whether GitHub confirmed success with HTTP 200/201")
    message: str = Field(default="Publishing completed successfully.")


class GitHubDiffLineRange(BaseModel):
    """Valid line range on the right side of a diff hunk."""
    start_line: int
    end_line: int
    added_lines: List[int] = Field(default_factory=list)
    context_lines: List[int] = Field(default_factory=list)

