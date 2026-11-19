"""Typed shared workflow state for LangGraph Multi-Agent Code Review Engine.

Enforces structured Pydantic schemas, append-only reducer channels for parallel agents,
and comprehensive tracking of findings, debates, logs, and token budgets.
"""

from datetime import datetime, timezone
import operator
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict
import uuid
from pydantic import BaseModel, Field


class FindingProposal(BaseModel):
    """Discrete code issue, vulnerability, or improvement proposed by a specialist agent."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = Field(description="Relative path of the target file in the repository")
    line_number: Optional[int] = Field(default=None, description="Starting line number in the diff")
    end_line_number: Optional[int] = Field(default=None, description="Ending line number in the diff")
    side: Literal["LEFT", "RIGHT"] = Field(default="RIGHT", description="Diff side: RIGHT for added/modified code")
    category: Literal["bug", "security", "performance", "architecture", "test", "style"] = Field(
        description="Category of the finding"
    )
    severity: Literal["critical", "high", "medium", "low", "info"] = Field(
        default="medium",
        description="Assessed severity level"
    )
    title: str = Field(description="Concise, actionable finding title")
    message: str = Field(description="Detailed explanation of the issue and why it poses a problem")
    suggested_patch: Optional[str] = Field(default=None, description="Unified diff or replacement code snippet")
    code_evidence: Optional[str] = Field(default=None, description="Exact code snippet from diff/context proving the issue")
    agent_name: str = Field(description="Specialist agent that discovered this issue")
    confidence_score: float = Field(default=0.9, ge=0.0, le=1.0, description="Confidence rating from 0.0 to 1.0")
    rule_id: Optional[str] = Field(default=None, description="Standard rule or CWE identifier (e.g., SEC-SQLI-001)")


class AgentFindingList(BaseModel):
    """Container for structured specialist agent output."""

    findings: List[FindingProposal] = Field(default_factory=list, description="List of detected findings")
    reasoning_summary: str = Field(
        default="Analysis completed.",
        description="High-level reasoning summary and evaluation of inspected changes"
    )


class AgentCritique(BaseModel):
    """Reviewer 2 challenge or critique of a specialist finding."""

    finding_id: str = Field(description="ID of the finding being evaluated")
    finding_title: str = Field(description="Title of the finding")
    is_supported: bool = Field(description="Whether the claim is substantiated by code evidence")
    challenge_reason: str = Field(description="Critique rationale, questioning assumptions or verifying context")
    suggested_action: Literal["approve", "reject", "modify"] = Field(
        default="approve",
        description="Recommendation for the Verification Arbiter"
    )
    duplicate_of_id: Optional[str] = Field(
        default=None,
        description="ID of existing finding if this is a redundant duplicate"
    )


class Reviewer2Output(BaseModel):
    """Container for Reviewer 2 adversarial critique and gap analysis."""

    critiques: List[AgentCritique] = Field(default_factory=list, description="Critique of each proposed finding")
    missed_scenarios: List[str] = Field(default_factory=list, description="Edge cases or unaddressed concerns in PR")
    reasoning_summary: str = Field(
        default="Adversarial evaluation complete.",
        description="Summary of adversarial examination"
    )


class VerifiedFinding(BaseModel):
    """Final finding verified against repository source code, execution paths, and evidence."""

    finding: FindingProposal = Field(description="The underlying finding proposal")
    status: Literal["verified", "uncertain", "rejected"] = Field(
        default="verified",
        description="Final verification verdict"
    )
    verification_reason: str = Field(description="Evidence or justification for verification decision")
    confidence_score: float = Field(default=0.95, ge=0.0, le=1.0, description="Calibrated confidence score")
    is_reproducible: bool = Field(default=True, description="Whether the issue is directly reproducible in code")
    execution_path_checked: bool = Field(default=True, description="Whether execution reachability was validated")


class VerificationOutput(BaseModel):
    """Container for Verification Arbiter output."""

    verified_findings: List[VerifiedFinding] = Field(
        default_factory=list,
        description="All evaluated findings with final verdicts"
    )
    reasoning_summary: str = Field(
        default="Verification arbiter review completed.",
        description="Arbiter summary and consensus reasoning"
    )
    consensus_notes: Optional[str] = Field(
        default=None,
        description="Notes on resolved disputes between specialists and Reviewer 2"
    )


class DiscussionItem(BaseModel):
    """Inter-agent message or consensus debate entry for the Agent Conference."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    review_id: Optional[str] = None
    finding_id: Optional[str] = None
    finding_title: Optional[str] = None
    agent_name: str
    message_type: Literal["proposal", "critique", "verification", "consensus", "dissent"] = "proposal"
    content: str
    file_context: Optional[str] = None
    is_verified: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentLogEntry(BaseModel):
    """Structured execution telemetry and resource audit log for an individual agent."""

    agent_name: str
    role: str
    status: Literal["completed", "failed", "timed_out", "skipped"] = "completed"
    execution_time_ms: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    findings_count: int = 0
    reasoning_summary: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewState(TypedDict):
    """Shared typed state passed between LangGraph nodes during multi-agent code review.

    Uses `operator.add` reducers to enable safe concurrent fan-out/fan-in execution
    across multiple specialist agents without race conditions.
    """

    # Identifiers & PR Metadata
    review_id: str
    pull_request_id: str
    repository_id: str
    commit_sha: str
    pr_title: str
    pr_description: str
    raw_diff: str

    # Context & Repository Intelligence
    changed_files: List[Dict[str, Any]]
    context_evidence: Dict[str, Any]
    pr_analysis: Dict[str, Any]

    # Concurrent Output Channels (Annotated reducers for parallel specialists)
    agent_findings: Annotated[List[FindingProposal], operator.add]
    agent_discussions: Annotated[List[DiscussionItem], operator.add]
    agent_execution_logs: Annotated[List[AgentLogEntry], operator.add]
    errors: Annotated[List[str], operator.add]

    # Deliberation & Verification Results
    verified_findings: List[VerifiedFinding]

    # Review Metrics & Final Output
    overall_score: float
    security_score: float
    performance_score: float
    quality_score: float
    review_summary: str

    # Resource Controls
    token_budget_remaining: int
    is_completed: bool
