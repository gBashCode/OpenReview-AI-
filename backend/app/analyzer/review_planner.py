"""Review Execution Planner and Multi-Agent Orchestration Allocator."""

from typing import Any, Dict, List, Set
from app.analyzer.schemas import (
    ChangeCategory,
    ChangedFileDTO,
    ChangedFunctionDTO,
    ReviewAgentRecommendationDTO,
    RiskFactorDTO,
    RiskLevel,
)


class ReviewPlanner:
    """Generates optimal multi-agent assignments, prioritized review files, and verification checklists."""

    def plan_review(
        self,
        change_categories: List[str],
        risk_level: RiskLevel,
        risk_factors: List[RiskFactorDTO],
        changed_files: List[ChangedFileDTO],
        changed_functions: List[ChangedFunctionDTO],
        affected_tests: List[str],
        missing_test_coverage: bool,
    ) -> Tuple[List[ReviewAgentRecommendationDTO], Dict[str, Any]]:
        """Allocates specialized AI review agents and constructs a phased review execution plan."""
        recommendations: List[ReviewAgentRecommendationDTO] = []

        is_security_sensitive = ChangeCategory.SECURITY_SENSITIVE.value in change_categories or any(
            "Authentication" in f.name or "Authorization" in f.name or "Payment" in f.name for f in risk_factors
        )
        is_perf_sensitive = ChangeCategory.PERFORMANCE_RELATED.value in change_categories
        is_arch_sensitive = ChangeCategory.REFACTORING.value in change_categories or any(
            "Public API" in f.name or "Database Migration" in f.name for f in risk_factors
        )

        # 1. Security Sentinel
        sec_evidence: Set[str] = set()
        for f in risk_factors:
            sec_evidence.update(f.evidence_files)

        recommendations.append(
            ReviewAgentRecommendationDTO(
                agent_name="Security Sentinel",
                agent_role="Application Security and Vulnerability Detection",
                priority="MANDATORY" if (is_security_sensitive or risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)) else "RECOMMENDED",
                rationale="Analyzes credential handling, token verification, injection vectors, and access controls.",
                focus_areas=sorted(list(sec_evidence)) if sec_evidence else [f.file_path for f in changed_files[:3]],
            )
        )

        # 2. Bug Hunter
        func_focus = [f.file_path for f in changed_files if f.category == "source_code"]
        recommendations.append(
            ReviewAgentRecommendationDTO(
                agent_name="Bug Hunter",
                agent_role="Edge Case, Regression, and Logic Flaw Detection",
                priority="MANDATORY",
                rationale="Scrutinizes branch boundaries, nil/null pointer checks, error handling, and logical traps.",
                focus_areas=func_focus[:5],
            )
        )

        # 3. Performance Optimizer
        recommendations.append(
            ReviewAgentRecommendationDTO(
                agent_name="Performance Optimizer",
                agent_role="Database Query, Concurrency, and Algorithmic Efficiency",
                priority="MANDATORY" if is_perf_sensitive else "RECOMMENDED",
                rationale="Inspects query efficiency, unindexed operations, memory allocations, and loop complexities.",
                focus_areas=[f.file_path for f in changed_files if f.category in ("source_code", "database_migration")][:3],
            )
        )

        # 4. Architecture Reviewer
        recommendations.append(
            ReviewAgentRecommendationDTO(
                agent_name="Architecture Reviewer",
                agent_role="System Design, Modularity, and API Contract Consistency",
                priority="MANDATORY" if is_arch_sensitive else "RECOMMENDED",
                rationale="Ensures clean architecture boundaries, backward-compatible API contracts, and tenant isolation.",
                focus_areas=[f.file_path for f in changed_files if "api" in f.file_path or "schema" in f.file_path][:4],
            )
        )

        # 5. Test Coverage Verifier
        recommendations.append(
            ReviewAgentRecommendationDTO(
                agent_name="Test Coverage Verifier",
                agent_role="Test Completeness and Regression Safety",
                priority="MANDATORY" if missing_test_coverage else "RECOMMENDED",
                rationale="Verifies unit test assertions, flags untested code paths, and recommends missing test cases.",
                focus_areas=affected_tests if affected_tests else [f.file_path for f in changed_files if f.category == "source_code"],
            )
        )

        # 6. Prioritize files for human & agent review
        sorted_files = sorted(
            changed_files,
            key=lambda x: (
                x.file_path in sec_evidence,
                x.additions + x.deletions,
            ),
            reverse=True,
        )
        priority_files = [f.file_path for f in sorted_files[:5]]

        # 7. Phased Review Execution Plan
        plan = {
            "execution_strategy": "Parallel Agent Conference with Consensus Verification",
            "phases": [
                {
                    "phase": 1,
                    "name": "Static Diff & Impact Parsing",
                    "status": "completed",
                    "description": "Unified diff parsed into AST line numbers and impact surface.",
                },
                {
                    "phase": 2,
                    "name": "Multi-Agent Autonomous Evaluation",
                    "status": "ready",
                    "allocated_agents": [r.agent_name for r in recommendations if r.priority == "MANDATORY"],
                    "description": "Allocated agents independently inspect changed functions and repository context.",
                },
                {
                    "phase": 3,
                    "name": "Agent Consensus Conference & AutoFix Generation",
                    "status": "pending",
                    "description": "Agents debate findings, eliminate false positives, and synthesize unified patches.",
                },
                {
                    "phase": 4,
                    "name": "GitHub Status & Review Comment Publishing",
                    "status": "pending",
                    "description": "Submit Check Run status badges, inline line comments, and executive summary table.",
                },
            ],
            "priority_files": priority_files,
            "verification_checklist": [
                "Verify authentication & authorization checks on all newly added routes.",
                "Confirm that error handling does not leak internal tracebacks or secrets.",
                "Ensure database migration scripts include safe backward-compatible rollback logic.",
                "Verify automated test coverage covers modified edge cases.",
            ],
        }

        return recommendations, plan
