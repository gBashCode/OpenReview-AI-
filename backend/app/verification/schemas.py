"""Evidence-based Finding Verification Engine Schemas.

Defines data contracts for the 12-step validation pipeline:
- Severity levels (Critical, High, Medium, Low, Informational)
- Verification statuses (Confirmed, High-confidence potential issue, Needs investigation, Rejected)
- Structured line ranges, source evidence, check results, and review policies.
- Keeps confidence strictly separate from severity.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TestRunBase(BaseModel):
    patch_id: str
    status: str = "pending"  # pending, running, passed, failed, error
    test_framework: str = "pytest"
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    execution_time_seconds: Optional[float] = None


class TestRunCreate(BaseModel):
    patch_id: str
    test_framework: Optional[str] = "pytest"


class TestRunRead(TestRunBase):
    id: str
    stdout_log: Optional[str] = None
    stderr_log: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FindingSeverity(str, Enum):
    """Assessed severity level representing impact and consequence."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"

    @classmethod
    def from_str(cls, val: str) -> "FindingSeverity":
        normalized = val.strip().capitalize()
        if normalized in ("Critical",):
            return cls.CRITICAL
        elif normalized in ("High",):
            return cls.HIGH
        elif normalized in ("Medium",):
            return cls.MEDIUM
        elif normalized in ("Low",):
            return cls.LOW
        elif normalized in ("Informational", "Info"):
            return cls.INFORMATIONAL
        # Default fallback
        return cls.MEDIUM


class VerificationStatus(str, Enum):
    """Evidence-based validation status representing certainty and proof."""

    CONFIRMED = "Confirmed"
    HIGH_CONFIDENCE = "High-confidence potential issue"
    NEEDS_INVESTIGATION = "Needs investigation"
    REJECTED = "Rejected"

    @classmethod
    def from_str(cls, val: str) -> "VerificationStatus":
        normalized = val.strip()
        for status in cls:
            if status.value.lower() == normalized.lower():
                return status
        if "confirm" in normalized.lower() or "verified" in normalized.lower() or "accepted" in normalized.lower():
            return cls.CONFIRMED
        elif "high" in normalized.lower():
            return cls.HIGH_CONFIDENCE
        elif "investig" in normalized.lower() or "uncertain" in normalized.lower():
            return cls.NEEDS_INVESTIGATION
        return cls.REJECTED


class CheckStatus(str, Enum):
    """Status of an individual verification check."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class LineRange(BaseModel):
    """1-indexed line number bounds in source code or diff."""

    start_line: int = Field(ge=1, description="Starting line number (1-indexed)")
    end_line: int = Field(ge=1, description="Ending line number (1-indexed)")

    @field_validator("end_line")
    @classmethod
    def validate_range(cls, v: int, info) -> int:
        start = info.data.get("start_line", 1)
        if v < start:
            raise ValueError(f"end_line ({v}) cannot be less than start_line ({start})")
        return v

    def overlaps(self, other: "LineRange", tolerance: int = 2) -> bool:
        """Determines if this range overlaps or is close to another line range."""
        return not (
            self.end_line + tolerance < other.start_line
            or self.start_line - tolerance > other.end_line
        )


class ValidationCheckResult(BaseModel):
    """Detailed result of an individual verification check."""

    check_name: str = Field(description="Name of the check (e.g. file_existence, static_analysis)")
    status: CheckStatus = Field(description="Execution result: passed, failed, warning, skipped")
    confidence_delta: float = Field(default=0.0, description="Confidence score modifier (-1.0 to +1.0)")
    reason: str = Field(description="Human-readable explanation of the check result")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic telemetry and metadata")


class CandidateFinding(BaseModel):
    """Raw finding proposed by an AI agent or analysis pass before verification."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(description="Proposed title")
    description: str = Field(description="Detailed issue explanation")
    file_path: str = Field(description="Repository relative file path")
    start_line: Optional[int] = Field(default=None, description="Starting line number")
    end_line: Optional[int] = Field(default=None, description="Ending line number")
    severity: str = Field(default="Medium", description="Proposed severity")
    confidence: float = Field(default=0.75, ge=0.0, le=1.0, description="Proposing agent confidence")
    root_cause: Optional[str] = Field(default=None, description="Technical underlying cause")
    impact: Optional[str] = Field(default=None, description="Potential harm or regression")
    source_evidence: Optional[str] = Field(default=None, description="Exact code snippet or proof")
    suggested_remediation: Optional[str] = Field(default=None, description="Fix instructions or patch")
    rule_id: Optional[str] = Field(default=None, description="Rule, CWE, or static analysis rule ID")
    category: Optional[str] = Field(default="bug", description="Finding category")
    agent_name: Optional[str] = Field(default="Specialist Agent", description="Proposer agent name")


class VerifiedFinding(BaseModel):
    """Fully verified finding conforming to all required evidence standards.

    Must contain all 11 required fields:
    - title
    - description
    - file_path
    - line_range
    - severity (Critical, High, Medium, Low, Informational)
    - confidence (0.0 to 1.0, separate from severity)
    - root_cause
    - impact
    - source_evidence
    - suggested_remediation
    - verification_status (Confirmed, High-confidence potential issue, Needs investigation, Rejected)
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    file_path: str
    line_range: LineRange
    severity: FindingSeverity
    confidence: float = Field(ge=0.0, le=1.0, description="Calibrated confidence (strictly separate from severity)")
    root_cause: str
    impact: str
    source_evidence: str
    suggested_remediation: str
    verification_status: VerificationStatus

    # Verification telemetry & actionability
    checks: List[ValidationCheckResult] = Field(default_factory=list)
    actionability_score: float = Field(default=0.0, ge=0.0, le=1.0)
    category: str = "bug"
    rule_id: Optional[str] = None
    agent_name: Optional[str] = None
    duplicate_of_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    is_publishable: bool = False
    publish_decision_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewPolicyConfig(BaseModel):
    """Configurable publishing policy to prevent false positives and noise."""

    policy_name: str = "Standard Review Policy"
    min_confidence: float = Field(default=0.70, ge=0.0, le=1.0)
    allowed_statuses: List[VerificationStatus] = Field(
        default_factory=lambda: [
            VerificationStatus.CONFIRMED,
            VerificationStatus.HIGH_CONFIDENCE,
        ]
    )
    min_severity: FindingSeverity = FindingSeverity.LOW
    block_duplicates: bool = True
    require_source_evidence: bool = True
    require_remediation: bool = True
    min_actionability: float = Field(default=0.60, ge=0.0, le=1.0)
    block_unverified_lines: bool = True
    allowed_categories: Optional[List[str]] = None


class VerificationBatchResult(BaseModel):
    """Summary of finding verification batch execution."""

    verified_findings: List[VerifiedFinding]
    total_candidates: int
    confirmed_count: int
    high_confidence_count: int
    needs_investigation_count: int
    rejected_count: int
    publishable_count: int
    execution_time_ms: int = 0
