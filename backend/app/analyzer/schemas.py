"""Pull Request Analysis Engine Pydantic Schemas."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChangeCategory(str, Enum):
    NEW_FEATURE = "New feature"
    BUG_FIX = "Bug fix"
    REFACTORING = "Refactoring"
    SECURITY_SENSITIVE = "Security-sensitive change"
    PERFORMANCE_RELATED = "Performance-related change"
    DEPENDENCY_UPDATE = "Dependency update"
    CONFIGURATION_CHANGE = "Configuration change"
    TEST_MODIFICATION = "Test modification"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DiffLineItem(BaseModel):
    line_type: str  # "+", "-", " "
    old_line_number: Optional[int] = None
    new_line_number: Optional[int] = None
    content: str


class DiffHunkDTO(BaseModel):
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    heading: Optional[str] = None
    lines: List[DiffLineItem] = []


class ChangedFileDTO(BaseModel):
    file_path: str
    old_path: Optional[str] = None
    status: str  # "modified", "added", "deleted", "renamed"
    additions: int
    deletions: int
    language: str
    category: str
    modified_line_numbers: List[int] = []
    patch: Optional[str] = None


class ChangedFunctionDTO(BaseModel):
    name: str
    kind: str  # "function", "method", "class"
    file_path: str
    line_number: int
    end_line_number: int
    signature: Optional[str] = None
    change_type: str = "modified"  # "added", "modified", "removed"


class RiskFactorDTO(BaseModel):
    name: str
    severity: RiskLevel
    description: str
    score_impact: float
    evidence_files: List[str] = []


class ReviewAgentRecommendationDTO(BaseModel):
    agent_name: str
    agent_role: str
    priority: str  # "MANDATORY", "RECOMMENDED", "OPTIONAL"
    rationale: str
    focus_areas: List[str] = []


class PRAnalysisRequest(BaseModel):
    raw_diff: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class PRAnalysisResult(BaseModel):
    """Complete, explainable analysis of a Pull Request's impact, risks, and review plan."""

    pr_number: int
    title: str
    summary: str
    total_additions: int
    total_deletions: int
    total_files_changed: int
    changed_files: List[ChangedFileDTO]
    changed_functions: List[ChangedFunctionDTO]
    change_categories: List[str]
    risk_score: float  # 0 to 100
    risk_level: RiskLevel
    risk_factors: List[RiskFactorDTO]
    complexity_level: ComplexityLevel
    complexity_details: Dict[str, Any]
    affected_modules: List[str]
    affected_tests: List[str]
    missing_test_coverage: bool
    related_code_references: Dict[str, Any] = {}
    recommended_review_agents: List[ReviewAgentRecommendationDTO]
    review_execution_plan: Dict[str, Any] = {}
