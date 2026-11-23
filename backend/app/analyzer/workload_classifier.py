"""Workload-Aware Infrastructure Complexity Classifier for AutoScaleX.

Calculates the computational and token-capacity weight of incoming Pull Requests
to dynamically route reviews to specialized Redis priority queues (reviews.fast,
reviews.standard, reviews.heavy) and inform Kubernetes/KEDA autoscaling controllers.
"""

from enum import Enum
import math
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkloadTier(str, Enum):
    """Categorical queue and scaling priority tiers."""
    FAST = "fast"          # Minimal diffs, single functions, docs, typo fixes (< 3s SLA)
    STANDARD = "standard"  # Typical multi-file PRs, components, endpoints (< 15s SLA)
    HEAVY = "heavy"        # Core architectural changes, migrations, mass refactors (< 60s SLA)


class WorkloadMetrics(BaseModel):
    """Granular factors that contribute to the PR computational weight."""
    changed_files_count: int = Field(default=0, ge=0)
    additions: int = Field(default=0, ge=0)
    deletions: int = Field(default=0, ge=0)
    total_churn: int = Field(default=0, ge=0)
    ast_symbol_count: int = Field(default=0, ge=0)
    cyclomatic_density: float = Field(default=0.0, ge=0.0)
    has_database_migration: bool = False
    has_security_sensitive_files: bool = False


class WorkloadScore(BaseModel):
    """Normalized workload score and execution quotas for AutoScaleX."""
    complexity_score: float = Field(
        ...,
        ge=1.0,
        le=100.0,
        description="Normalized difficulty/compute index from 1.0 (trivial) to 100.0 (extreme)",
    )
    tier: WorkloadTier = Field(
        ...,
        description="Assigned queue priority: fast, standard, or heavy",
    )
    estimated_tokens: int = Field(
        ...,
        ge=500,
        description="Projected LLM token consumption across all council agents",
    )
    estimated_duration_seconds: float = Field(
        ...,
        ge=1.0,
        description="Estimated processing time for LangGraph conference pass",
    )
    recommended_agent_count: int = Field(
        ...,
        ge=1,
        le=8,
        description="Optimal number of specialist agents needed for this workload level",
    )
    scaling_weight: float = Field(
        ...,
        ge=0.1,
        le=5.0,
        description="Multiplier for KEDA Prometheus metric backlog aggregation",
    )
    timeout_seconds: int = Field(
        ...,
        description="Bounded execution ceiling before guaranteed fallback termination",
    )
    metrics: WorkloadMetrics
    reasons: List[str] = Field(default_factory=list)


class WorkloadClassifier:
    """Evaluates pull request dimensions into workload weights and queue tiers."""

    SECURITY_SENSITIVE_PATTERNS = [
        r"auth",
        r"token",
        r"secret",
        r"password",
        r"crypto",
        r"session",
        r"security",
        r"permission",
        r"middleware",
    ]

    MIGRATION_PATTERNS = [
        r"alembic",
        r"migration",
        r"migrations",
        r"\.sql$",
        r"db[\\/]schema",
        r"database[\\/]schema",
    ]

    CYCLOMATIC_KEYWORDS = [
        r"\bif\b",
        r"\belif\b",
        r"\belse\b",
        r"\bswitch\b",
        r"\bcase\b",
        r"\bfor\b",
        r"\bwhile\b",
        r"\btry\b",
        r"\bexcept\b",
        r"\bcatch\b",
        r"&&",
        r"\|\|",
        r"\?",
    ]

    def classify(
        self,
        changed_files_count: int,
        additions: int,
        deletions: int,
        file_paths: Optional[List[str]] = None,
        raw_diff: Optional[str] = None,
        ast_symbol_count: Optional[int] = None,
    ) -> WorkloadScore:
        """Computes comprehensive workload score and AutoScaleX scheduling tier."""
        # Normalize baseline metrics
        safe_files = max(0, changed_files_count)
        safe_additions = max(0, additions)
        safe_deletions = max(0, deletions)
        total_churn = safe_additions + safe_deletions
        reasons: List[str] = []

        # 1. Inspect file path domain markers
        has_migrations = False
        has_security = False
        paths = file_paths or []

        if paths:
            mig_regex = re.compile("|".join(self.MIGRATION_PATTERNS), re.IGNORECASE)
            sec_regex = re.compile("|".join(self.SECURITY_SENSITIVE_PATTERNS), re.IGNORECASE)

            for p in paths:
                if mig_regex.search(p):
                    has_migrations = True
                if sec_regex.search(p):
                    has_security = True

        # 2. Inspect cyclomatic branching if raw diff supplied
        cyclomatic_count = 0
        if raw_diff:
            cyc_regex = re.compile("|".join(self.CYCLOMATIC_KEYWORDS))
            for line in raw_diff.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    matches = cyc_regex.findall(line)
                    cyclomatic_count += len(matches)

        cyc_density = (cyclomatic_count / max(1, safe_additions)) if safe_additions > 0 else 0.0

        # 3. Factor calculations
        # A: File breadth factor (0 to 35 pts)
        file_factor = min(safe_files * 2.5, 35.0)
        if safe_files > 15:
            reasons.append(f"Broad multi-file surface area ({safe_files} files)")

        # B: Line churn volume factor (0 to 40 pts)
        # Additions weighted higher than deletions because new code requires syntax AST & security analysis
        churn_factor = min((safe_additions * 1.0 + safe_deletions * 0.35) / 15.0, 40.0)
        if total_churn > 400:
            reasons.append(f"Substantial code churn ({total_churn} lines changed)")

        # C: AST symbol / branch complexity (0 to 25 pts)
        resolved_symbols = ast_symbol_count if ast_symbol_count is not None else int(safe_additions / 8)
        ast_factor = min(resolved_symbols * 0.8 + min(cyclomatic_count * 0.5, 10.0), 25.0)

        raw_score = file_factor + churn_factor + ast_factor

        # Multiplier adjustments for mission-critical changes
        if has_migrations:
            raw_score += 15.0
            reasons.append("Includes schema/database migrations requiring cross-version safety review")

        if has_security:
            raw_score += 12.0
            reasons.append("Touches authentication or security-sensitive boundaries")

        # Clamp normalized score strictly between 1.0 and 100.0
        final_score = round(max(1.0, min(100.0, raw_score)), 2)

        # 4. Tier and quota allocation
        if final_score <= 18.0 and safe_files <= 3 and total_churn <= 80 and not has_migrations:
            tier = WorkloadTier.FAST
            reasons.insert(0, "Fast track: Focused, low-risk change")
            estimated_tokens = int(1200 + total_churn * 4.0)
            duration_secs = 2.5
            recommended_agents = 3  # Security Sentinel, Bug Hunter, Lead Arbiter
            scaling_weight = 0.25   # Light footprint
            timeout_secs = 15
        elif final_score > 55.0 or safe_files > 15 or total_churn > 600 or has_migrations:
            tier = WorkloadTier.HEAVY
            reasons.insert(0, "Heavy track: Complex multi-module architectural review")
            estimated_tokens = int(8000 + safe_files * 800 + total_churn * 6.0)
            duration_secs = 18.0
            recommended_agents = 8  # Full council + Reviewer #2 + Verification Arbiter
            scaling_weight = 3.0    # Demands dedicated worker slice
            timeout_secs = 90
        else:
            tier = WorkloadTier.STANDARD
            reasons.insert(0, "Standard track: Moderate feature development")
            estimated_tokens = int(3500 + total_churn * 5.0)
            duration_secs = 6.5
            recommended_agents = 5  # Standard 5-specialist council
            scaling_weight = 1.0    # Baseline KEDA weight
            timeout_secs = 45

        metrics = WorkloadMetrics(
            changed_files_count=safe_files,
            additions=safe_additions,
            deletions=safe_deletions,
            total_churn=total_churn,
            ast_symbol_count=resolved_symbols,
            cyclomatic_density=round(cyc_density, 3),
            has_database_migration=has_migrations,
            has_security_sensitive_files=has_security,
        )

        return WorkloadScore(
            complexity_score=final_score,
            tier=tier,
            estimated_tokens=estimated_tokens,
            estimated_duration_seconds=duration_secs,
            recommended_agent_count=recommended_agents,
            scaling_weight=scaling_weight,
            timeout_seconds=timeout_secs,
            metrics=metrics,
            reasons=reasons,
        )


# Global singleton instance
workload_classifier = WorkloadClassifier()
