"""AI Agent and Discussion Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ReviewAgentBase(BaseModel):
    review_id: str
    agent_name: str
    role: str
    status: str = "idle"
    model_name: Optional[str] = None
    reasoning_summary: Optional[str] = None
    confidence_score: Optional[float] = None
    findings_count: int = 0
    execution_time_ms: Optional[int] = None


class ReviewAgentCreate(ReviewAgentBase):
    pass


class ReviewAgentRead(ReviewAgentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentDiscussionBase(BaseModel):
    review_id: Optional[str] = None
    finding_id: Optional[str] = None
    agent_name: str
    message_type: str = "proposal"  # proposal, critique, verification, consensus, dissent
    content: str
    file_context: Optional[str] = None
    is_verified: bool = False


class AgentDiscussionCreate(AgentDiscussionBase):
    pass


class AgentDiscussionRead(AgentDiscussionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
