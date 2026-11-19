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
    evidence: Optional[str] = None
    source_reference: Optional[str] = None
    position: str = "proposal"  # proposal, challenge, rebuttal, context_supply, verdict, concession
    final_decision: Optional[str] = None  # Accepted, Rejected, Needs investigation, Duplicate, Uncertain
    round_number: int = 1
    is_verified: bool = False


class AgentDiscussionCreate(AgentDiscussionBase):
    pass


class AgentDiscussionRead(AgentDiscussionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConferenceFindingThread(BaseModel):
    """A threaded multi-agent debate stream anchored to a specific finding."""

    finding_id: str
    file_path: str
    line_number: Optional[int] = None
    title: str
    category: str
    severity: str
    proposing_agent: str
    discussion_state: str = "Accepted"  # Accepted, Rejected, Needs investigation, Duplicate, Uncertain
    evidence: Optional[str] = None
    suggested_patch: Optional[str] = None
    messages: list[AgentDiscussionRead] = []


class ConferenceSessionResponse(BaseModel):
    """Full conference session data for live UI rendering."""

    review_id: str
    pull_request_id: str
    commit_sha: str
    status: str
    total_rounds: int
    discussion_threads: list[ConferenceFindingThread]
    agents: list[ReviewAgentRead]
    summary_metrics: dict[str, Any]
