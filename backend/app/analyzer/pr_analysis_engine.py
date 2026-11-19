"""Autonomous Pull Request Analysis Engine Orchestrator."""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzer.diff_parser import ParsedDiffFile, UnifiedDiffParser
from app.analyzer.impact_detector import ImpactDetector
from app.analyzer.review_planner import ReviewPlanner
from app.analyzer.risk_scorer import RiskScorer
from app.analyzer.schemas import (
    ChangedFileDTO,
    ChangedFunctionDTO,
    PRAnalysisResult,
    ReviewAgentRecommendationDTO,
    RiskFactorDTO,
)
from app.core.logging import get_logger
from app.indexing.context_retriever import ContextRetriever
from app.indexing.dependency_graph import DependencyGraph
from app.indexing.models import CodeSymbol, RepositoryIndex

logger = get_logger("openreview.analyzer.engine")


class PRAnalysisEngine:
    """End-to-end analyzer combining Git diff parsing, AST symbol mapping,
    sensitive change heuristics, risk scoring, and review planning.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.diff_parser = UnifiedDiffParser()
        self.impact_detector = ImpactDetector()
        self.risk_scorer = RiskScorer()
        self.planner = ReviewPlanner()
        self.retriever = ContextRetriever(session) if session else None

    async def analyze_pull_request(
        self,
        raw_diff: str,
        pr_number: int = 1,
        title: str = "Pull Request",
        description: str = "",
        repository_id: Optional[str] = None,
    ) -> PRAnalysisResult:
        """Executes full architectural and impact analysis on a PR diff."""
        # 1. Parse unified diff
        parsed_files = self.diff_parser.parse(raw_diff)
        changed_files_dto: List[ChangedFileDTO] = [self.diff_parser.to_dto(pf) for pf in parsed_files]

        total_additions = sum(pf.additions for pf in parsed_files)
        total_deletions = sum(pf.deletions for pf in parsed_files)

        # 2. Fetch repository index and context if session and repository_id provided
        repo_symbols: List[Any] = []
        dep_graph: Optional[DependencyGraph] = None
        related_references: Dict[str, Any] = {}

        if self.session and repository_id:
            try:
                # Latest completed index
                idx_stmt = (
                    select(RepositoryIndex)
                    .where(
                        RepositoryIndex.repository_id == repository_id,
                        RepositoryIndex.status == "completed",
                    )
                    .order_by(RepositoryIndex.created_at.desc())
                )
                index = (await self.session.execute(idx_stmt)).scalars().first()
                if index:
                    # Fetch symbols
                    sym_stmt = select(CodeSymbol).where(CodeSymbol.index_id == index.id)
                    repo_symbols = list((await self.session.execute(sym_stmt)).scalars().all())

                    if index.summary_json and "dependencies" in index.summary_json:
                        dep_graph = DependencyGraph.from_dict(index.summary_json["dependencies"])

                    # Context retrieval
                    if self.retriever:
                        changed_input = [
                            {
                                "file_path": f.file_path,
                                "changed_lines": f.modified_line_numbers,
                            }
                            for f in changed_files_dto
                        ]
                        evidence = await self.retriever.retrieve_pr_context(
                            repository_id=repository_id,
                            changed_files=changed_input,
                            top_k_semantic=3,
                        )
                        related_references = {
                            "function_callers": [
                                {"caller": c.caller_name, "callee": c.callee_name, "file": c.file_path, "line": c.line_number}
                                for c in evidence.function_callers
                            ],
                            "imported_modules": [
                                {"module": m.module, "file": m.file_path}
                                for m in evidence.imported_modules
                            ],
                            "related_tests": [
                                {"test_file": t.test_file_path, "target_file": t.target_file_path}
                                for t in evidence.related_tests
                            ],
                            "semantic_matches": [
                                {"file": sm.file_path, "lines": f"{sm.start_line}-{sm.end_line}", "similarity": sm.similarity}
                                for sm in evidence.semantic_matches
                            ],
                        }
            except Exception as ctx_err:
                logger.warning(f"Failed to fetch repository context for analysis: {ctx_err}")

        # 3. Identify modified functions
        changed_functions = self.impact_detector.identify_modified_functions(
            parsed_files, repo_symbols=repo_symbols
        )

        # 4. Sensitive changes detection
        sensitive_factors = self.impact_detector.detect_sensitive_changes(parsed_files)

        # 5. Classify change categories
        change_categories = self.impact_detector.classify_change_types(
            parsed_files, pr_title=title, pr_description=description, sensitive_factors=sensitive_factors
        )

        # 6. Affected modules
        affected_modules = self.impact_detector.detect_affected_modules(parsed_files)

        # 7. Affected tests and coverage gap detection
        affected_tests, missing_test_coverage = self.impact_detector.detect_affected_tests(
            parsed_files, dep_graph=dep_graph
        )

        # 8. Complexity estimation
        complexity_level, complexity_details = self.risk_scorer.estimate_complexity(
            parsed_files, changed_functions
        )

        # 9. Explainable risk scoring
        risk_score, risk_level, all_risk_factors = self.risk_scorer.calculate_risk(
            complexity_level=complexity_level,
            sensitive_factors=sensitive_factors,
            missing_test_coverage=missing_test_coverage,
            affected_modules_count=len(affected_modules),
            file_count=len(parsed_files),
        )

        # 10. Multi-Agent Review Planning
        recommended_agents, review_plan = self.planner.plan_review(
            change_categories=change_categories,
            risk_level=risk_level,
            risk_factors=all_risk_factors,
            changed_files=changed_files_dto,
            changed_functions=changed_functions,
            affected_tests=affected_tests,
            missing_test_coverage=missing_test_coverage,
        )

        # 11. Generate PR Executive Summary
        summary = self._generate_executive_summary(
            pr_number=pr_number,
            title=title,
            categories=change_categories,
            risk_level=risk_level,
            risk_score=risk_score,
            total_additions=total_additions,
            total_deletions=total_deletions,
            file_count=len(parsed_files),
            func_count=len(changed_functions),
            missing_test_coverage=missing_test_coverage,
        )

        return PRAnalysisResult(
            pr_number=pr_number,
            title=title,
            summary=summary,
            total_additions=total_additions,
            total_deletions=total_deletions,
            total_files_changed=len(parsed_files),
            changed_files=changed_files_dto,
            changed_functions=changed_functions,
            change_categories=change_categories,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=all_risk_factors,
            complexity_level=complexity_level,
            complexity_details=complexity_details,
            affected_modules=affected_modules,
            affected_tests=affected_tests,
            missing_test_coverage=missing_test_coverage,
            related_code_references=related_references,
            recommended_review_agents=recommended_agents,
            review_execution_plan=review_plan,
        )

    def _generate_executive_summary(
        self,
        pr_number: int,
        title: str,
        categories: List[str],
        risk_level: Any,
        risk_score: float,
        total_additions: int,
        total_deletions: int,
        file_count: int,
        func_count: int,
        missing_test_coverage: bool,
    ) -> str:
        cat_str = ", ".join(categories)
        summary = (
            f"**PR #{pr_number}: {title}**\n\n"
            f"• **Classifications**: {cat_str}\n"
            f"• **Risk Assessment**: **{risk_level.value}** ({risk_score}/100)\n"
            f"• **Change Scope**: {file_count} files touched, {func_count} functions/methods affected (+{total_additions} / -{total_deletions} lines)"
        )
        if missing_test_coverage:
            summary += "\n• ⚠️ **Warning**: Source code modified without accompanying automated test updates."
        return summary
