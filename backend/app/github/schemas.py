"""GitHub Integration Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class GitHubInstallationBase(BaseModel):
    installation_id: int
    account_login: str
    account_type: str = "User"  # User, Organization
    permissions_json: Optional[str] = None


class GitHubInstallationCreate(GitHubInstallationBase):
    organization_id: str


class GitHubInstallationRead(GitHubInstallationBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GitHubWebhookPayload(BaseModel):
    action: str
    repository: Optional[Dict[str, Any]] = None
    pull_request: Optional[Dict[str, Any]] = None
    installation: Optional[Dict[str, Any]] = None
    sender: Optional[Dict[str, Any]] = None
