"""Review and ReviewComment schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReviewCommentBase(BaseModel):
    file_path: str = Field(..., examples=["src/auth/jwt.py"])
    line_number: Optional[int] = Field(None, examples=[45])
    end_line_number: Optional[int] = None
    side: str = Field(default="RIGHT")
    category: str = Field(..., examples=["security"])
    severity: str = Field(..., examples=["critical"])
    title: str = Field(..., examples=["Hardcoded JWT Secret Detected"])
    message: str = Field(..., examples=["Do not hardcode secrets directly into source code."])
    suggested_patch: Optional[str] = None
    is_resolved: bool = False


class ReviewCommentCreate(ReviewCommentBase):
    pass


class ReviewCommentRead(ReviewCommentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    review_id: str
    github_comment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class ReviewBase(BaseModel):
    commit_sha: str = Field(..., max_length=40)
    status: str = Field(default="pending")
    summary: Optional[str] = None
    score: Optional[float] = None
    security_score: Optional[float] = None
    performance_score: Optional[float] = None
    quality_score: Optional[float] = None


class ReviewCreate(BaseModel):
    pull_request_id: str
    commit_sha: str


class ReviewRead(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pull_request_id: str
    findings_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReviewDetailRead(ReviewRead):
    comments: List[ReviewCommentRead] = []
