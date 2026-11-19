"""Explainable Pull Request Complexity and Review Risk Scoring Engine."""

import re
from typing import Any, Dict, List, Tuple
from app.analyzer.diff_parser import ParsedDiffFile
from app.analyzer.schemas import (
    ChangedFunctionDTO,
    ComplexityLevel,
    RiskFactorDTO,
    RiskLevel,
)


class RiskScorer:
    """Calculates granular, explainable risk scores and architectural complexity metrics."""

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

    def estimate_complexity(
        self,
        parsed_files: List[ParsedDiffFile],
        changed_functions: List[ChangedFunctionDTO],
    ) -> Tuple[ComplexityLevel, Dict[str, Any]]:
        """Estimates code churn, branching statement increases, and change complexity."""
        total_additions = sum(f.additions for f in parsed_files)
        total_deletions = sum(f.deletions for f in parsed_files)
        churn = total_additions + total_deletions
        file_count = len(parsed_files)
        func_count = len(changed_functions)

        # Count cyclomatic complexity indicators in added lines
        cyclomatic_count = 0
        pattern = re.compile("|".join(self.CYCLOMATIC_KEYWORDS))

        for pf in parsed_files:
            for _, line in pf.added_lines:
                matches = pattern.findall(line)
                cyclomatic_count += len(matches)

        # Classify Complexity Level
        if churn > 800 or cyclomatic_count > 25 or file_count > 15:
            level = ComplexityLevel.CRITICAL
        elif churn > 300 or cyclomatic_count > 12 or file_count >= 8:
            level = ComplexityLevel.HIGH
        elif churn > 60 or cyclomatic_count >= 4 or file_count >= 3:
            level = ComplexityLevel.MEDIUM
        else:
            level = ComplexityLevel.LOW

        details = {
            "total_churn": churn,
            "additions": total_additions,
            "deletions": total_deletions,
            "files_touched": file_count,
            "functions_modified": func_count,
            "branching_statements_added": cyclomatic_count,
            "level": level.value,
        }

        return level, details

    def calculate_risk(
        self,
        complexity_level: ComplexityLevel,
        sensitive_factors: List[RiskFactorDTO],
        missing_test_coverage: bool,
        affected_modules_count: int,
        file_count: int,
    ) -> Tuple[float, RiskLevel, List[RiskFactorDTO]]:
        """Computes a transparent 0-100 review risk score with itemized factors."""
        all_factors: List[RiskFactorDTO] = list(sensitive_factors)
        score = 0.0

        # 1. Base complexity score contribution
        complexity_points = {
            ComplexityLevel.LOW: 10.0,
            ComplexityLevel.MEDIUM: 20.0,
            ComplexityLevel.HIGH: 35.0,
            ComplexityLevel.CRITICAL: 50.0,
        }.get(complexity_level, 10.0)

        score += complexity_points
        all_factors.append(
            RiskFactorDTO(
                name=f"Complexity Level: {complexity_level.value}",
                severity=RiskLevel(complexity_level.value),
                description=f"Baseline risk derived from code churn, cyclomatic branching, and file count.",
                score_impact=complexity_points,
                evidence_files=[],
            )
        )

        # 2. Add sensitive factors
        for factor in sensitive_factors:
            score += factor.score_impact

        # 3. Missing Test Coverage penalty
        if missing_test_coverage:
            test_penalty = 20.0
            score += test_penalty
            all_factors.append(
                RiskFactorDTO(
                    name="Missing Test Coverage",
                    severity=RiskLevel.HIGH,
                    description="Production source code modified without accompanying automated test updates.",
                    score_impact=test_penalty,
                    evidence_files=[],
                )
            )

        # 4. Blast Radius (multiple modules touched)
        if affected_modules_count >= 3 or file_count >= 8:
            blast_penalty = 15.0
            score += blast_penalty
            all_factors.append(
                RiskFactorDTO(
                    name="Broad Blast Radius",
                    severity=RiskLevel.MEDIUM,
                    description=f"Changes span {affected_modules_count} distinct modules and {file_count} files.",
                    score_impact=blast_penalty,
                    evidence_files=[],
                )
            )

        # Clamp score to [0.0, 100.0]
        final_score = min(100.0, max(5.0, score))

        # Determine overall Risk Level
        if final_score >= 75.0:
            risk_level = RiskLevel.CRITICAL
        elif final_score >= 50.0:
            risk_level = RiskLevel.HIGH
        elif final_score >= 25.0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return round(final_score, 1), risk_level, all_factors
