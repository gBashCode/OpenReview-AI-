"""Evidence-Based Finding Verification Engine.

Performs 12-step validation to eliminate false positives, verify source code evidence,
calibrate confidence independently from severity, and enforce configurable publishing policies:

1. File existence.
2. Line number validation.
3. Source snippet validation.
4. Surrounding code analysis (defensive guards & mitigation detection).
5. Repository context validation.
6. Static analysis (AST syntax & anti-pattern checks).
7. Type checking where available.
8. Test reproduction where feasible.
9. Duplicate detection.
10. Severity assessment (objective impact ranking).
11. Confidence calibration (separate from severity).
12. Actionability assessment.
"""

import ast
import os
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.logging import get_logger
from app.verification.policy import ReviewPolicyEngine
from app.verification.schemas import (
    CandidateFinding,
    CheckStatus,
    FindingSeverity,
    LineRange,
    ReviewPolicyConfig,
    ValidationCheckResult,
    VerificationBatchResult,
    VerificationStatus,
    VerifiedFinding,
)

logger = get_logger("openreview.verification.engine")


class FindingVerificationEngine:
    """Orchestrates comprehensive 12-step validation for AI code review findings."""

    def __init__(self, policy: Optional[ReviewPolicyConfig] = None):
        self.policy = policy or ReviewPolicyEngine.get_standard_policy()

    def verify_finding(
        self,
        candidate: CandidateFinding,
        repository_files: Optional[Dict[str, str]] = None,
        changed_files: Optional[List[Dict[str, Any]]] = None,
        existing_findings: Optional[List[VerifiedFinding]] = None,
        test_files: Optional[List[str]] = None,
        context_evidence: Optional[Dict[str, Any]] = None,
    ) -> VerifiedFinding:
        """Executes the full 12-step validation pipeline on a single candidate finding."""
        repo_files = repository_files or {}
        norm_path = candidate.file_path.replace("\\", "/").strip("/")

        file_content = repo_files.get(norm_path)
        if file_content is None and os.path.isfile(candidate.file_path):
            try:
                with open(candidate.file_path, "r", encoding="utf-8", errors="replace") as f:
                    file_content = f.read()
            except Exception:
                file_content = None

        checks: List[ValidationCheckResult] = []
        is_fatal = False
        fatal_reason = ""
        is_false_positive = False

        # --- Check 1: File Existence ---
        c1, file_exists = self._check_file_existence(norm_path, repo_files, changed_files)
        checks.append(c1)
        if not file_exists:
            is_fatal = True
            fatal_reason = c1.reason

        # --- Check 2: Line Number Validation ---
        c2, line_range = self._check_line_numbers(candidate, file_content)
        checks.append(c2)
        if c2.status == CheckStatus.FAILED and not is_fatal:
            is_fatal = True
            fatal_reason = c2.reason

        # --- Check 3: Source Snippet Validation ---
        c3, snippet_match_info = self._check_source_snippet(
            candidate, file_content, line_range, file_exists
        )
        checks.append(c3)
        if c3.status == CheckStatus.FAILED and not is_fatal:
            # Missing or completely fabricated snippet
            is_fatal = True
            fatal_reason = c3.reason

        # --- Check 4: Surrounding Code Analysis (False Positive Mitigation) ---
        c4, mitigated = self._check_surrounding_code(candidate, file_content, line_range)
        checks.append(c4)
        if mitigated:
            is_false_positive = True
            if not is_fatal:
                fatal_reason = c4.reason

        # --- Check 5: Repository Context Validation ---
        c5 = self._check_repository_context(candidate, norm_path, context_evidence)
        checks.append(c5)

        # --- Check 6: Static Analysis ---
        c6 = self._check_static_analysis(candidate, file_content, norm_path)
        checks.append(c6)

        # --- Check 7: Type Checking Where Available ---
        c7 = self._check_type_annotations(candidate, file_content, norm_path)
        checks.append(c7)

        # --- Check 8: Test Reproduction Where Feasible ---
        c8 = self._check_test_reproduction(candidate, norm_path, test_files)
        checks.append(c8)

        # --- Check 9: Duplicate Detection ---
        c9, duplicate_of_id = self._check_duplicates(candidate, line_range, existing_findings)
        checks.append(c9)
        if duplicate_of_id and not is_fatal:
            fatal_reason = c9.reason

        # --- Check 10: Severity Assessment (Objective Impact) ---
        c10, assessed_severity = self._check_severity_assessment(candidate)
        checks.append(c10)

        # --- Check 11: Confidence Calibration (Separated from Severity) ---
        c11, calibrated_confidence, status = self._calibrate_confidence(
            candidate=candidate,
            checks=checks,
            is_fatal=is_fatal,
            is_false_positive=is_false_positive,
            duplicate_of_id=duplicate_of_id,
        )
        checks.append(c11)

        # --- Check 12: Actionability Assessment ---
        c12, actionability_score = self._check_actionability(candidate, line_range)
        checks.append(c12)

        # Build VerifiedFinding with all 11 mandatory fields
        root_cause = candidate.root_cause or self._infer_root_cause(candidate)
        impact = candidate.impact or self._infer_impact(candidate, assessed_severity)
        source_evidence = candidate.source_evidence or (
            snippet_match_info.get("extracted_code") if snippet_match_info else ""
        ) or "No code snippet provided."
        suggested_remediation = candidate.suggested_remediation or (
            "Review and sanitize input handling at the specified line range."
        )

        verified = VerifiedFinding(
            id=candidate.id,
            title=candidate.title,
            description=candidate.description,
            file_path=norm_path,
            line_range=line_range,
            severity=assessed_severity,
            confidence=calibrated_confidence,
            root_cause=root_cause,
            impact=impact,
            source_evidence=source_evidence,
            suggested_remediation=suggested_remediation,
            verification_status=status,
            checks=checks,
            actionability_score=actionability_score,
            category=candidate.category or "bug",
            rule_id=candidate.rule_id,
            agent_name=candidate.agent_name,
            duplicate_of_id=duplicate_of_id,
            rejection_reason=fatal_reason if status == VerificationStatus.REJECTED else None,
        )

        # Apply Review Policy to decide publishability
        policy_decision = ReviewPolicyEngine.evaluate(verified, self.policy)
        verified.is_publishable = policy_decision.is_publishable
        verified.publish_decision_reason = policy_decision.reason

        return verified

    def verify_batch(
        self,
        candidates: List[CandidateFinding],
        repository_files: Optional[Dict[str, str]] = None,
        changed_files: Optional[List[Dict[str, Any]]] = None,
        test_files: Optional[List[str]] = None,
        context_evidence: Optional[Dict[str, Any]] = None,
        policy: Optional[ReviewPolicyConfig] = None,
    ) -> VerificationBatchResult:
        """Executes verification across a batch of candidate findings with inter-finding deduplication."""
        start_time = time.perf_counter()
        active_policy = policy or self.policy
        engine = FindingVerificationEngine(policy=active_policy)

        verified_list: List[VerifiedFinding] = []

        for candidate in candidates:
            vf = engine.verify_finding(
                candidate=candidate,
                repository_files=repository_files,
                changed_files=changed_files,
                existing_findings=verified_list,
                test_files=test_files,
                context_evidence=context_evidence,
            )
            verified_list.append(vf)

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        confirmed = sum(1 for f in verified_list if f.verification_status == VerificationStatus.CONFIRMED)
        high_conf = sum(1 for f in verified_list if f.verification_status == VerificationStatus.HIGH_CONFIDENCE)
        needs_inv = sum(1 for f in verified_list if f.verification_status == VerificationStatus.NEEDS_INVESTIGATION)
        rejected = sum(1 for f in verified_list if f.verification_status == VerificationStatus.REJECTED)
        publishable = sum(1 for f in verified_list if f.is_publishable)

        return VerificationBatchResult(
            verified_findings=verified_list,
            total_candidates=len(candidates),
            confirmed_count=confirmed,
            high_confidence_count=high_conf,
            needs_investigation_count=needs_inv,
            rejected_count=rejected,
            publishable_count=publishable,
            execution_time_ms=duration_ms,
        )

    # -------------------------------------------------------------------------
    # Individual Verification Check Implementations (1 to 12)
    # -------------------------------------------------------------------------

    def _check_file_existence(
        self,
        file_path: str,
        repo_files: Dict[str, str],
        changed_files: Optional[List[Dict[str, Any]]],
    ) -> Tuple[ValidationCheckResult, bool]:
        """Check 1: Validates that the referenced file exists in repository or PR."""
        if file_path in repo_files:
            return (
                ValidationCheckResult(
                    check_name="file_existence",
                    status=CheckStatus.PASSED,
                    confidence_delta=+0.05,
                    reason=f"File '{file_path}' exists in repository workspace.",
                ),
                True,
            )

        if changed_files:
            for cf in changed_files:
                cf_path = cf.get("file_path") or cf.get("filename") or ""
                if cf_path.replace("\\", "/").strip("/") == file_path:
                    return (
                        ValidationCheckResult(
                            check_name="file_existence",
                            status=CheckStatus.PASSED,
                            confidence_delta=+0.05,
                            reason=f"File '{file_path}' found in PR changed files.",
                        ),
                        True,
                    )

        if os.path.isfile(file_path):
            return (
                ValidationCheckResult(
                    check_name="file_existence",
                    status=CheckStatus.PASSED,
                    confidence_delta=+0.05,
                    reason=f"File '{file_path}' confirmed on local filesystem.",
                ),
                True,
            )

        # File does not exist anywhere: Hallucination!
        return (
            ValidationCheckResult(
                check_name="file_existence",
                status=CheckStatus.FAILED,
                confidence_delta=-1.0,
                reason=f"File '{file_path}' does not exist in repository or PR changes.",
            ),
            False,
        )

    def _check_line_numbers(
        self,
        candidate: CandidateFinding,
        file_content: Optional[str],
    ) -> Tuple[ValidationCheckResult, LineRange]:
        """Check 2: Validates line bounds and positive indexing."""
        raw_start = candidate.start_line
        raw_end = candidate.end_line or raw_start

        if raw_start is None or raw_start <= 0:
            default_range = LineRange(start_line=1, end_line=1)
            return (
                ValidationCheckResult(
                    check_name="line_number_validation",
                    status=CheckStatus.FAILED,
                    confidence_delta=-0.8,
                    reason=f"Invalid start line ({raw_start}); line numbers must be positive integers.",
                ),
                default_range,
            )

        end_val = raw_end if raw_end and raw_end >= raw_start else raw_start
        target_range = LineRange(start_line=raw_start, end_line=end_val)

        if file_content is not None:
            total_lines = len(file_content.splitlines())
            if target_range.start_line > total_lines:
                return (
                    ValidationCheckResult(
                        check_name="line_number_validation",
                        status=CheckStatus.FAILED,
                        confidence_delta=-0.9,
                        reason=f"Invalid line range [{target_range.start_line}, {target_range.end_line}]: exceeds total file length of {total_lines} lines.",
                        details={"total_file_lines": total_lines},
                    ),
                    target_range,
                )

        return (
            ValidationCheckResult(
                check_name="line_number_validation",
                status=CheckStatus.PASSED,
                confidence_delta=+0.05,
                reason=f"Line range [{target_range.start_line}, {target_range.end_line}] is valid.",
            ),
            target_range,
        )

    def _check_source_snippet(
        self,
        candidate: CandidateFinding,
        file_content: Optional[str],
        line_range: LineRange,
        file_exists: bool,
    ) -> Tuple[ValidationCheckResult, Dict[str, Any]]:
        """Check 3: Validates that claimed source evidence matches code at specified lines."""
        if not file_exists or file_content is None:
            return (
                ValidationCheckResult(
                    check_name="source_snippet_validation",
                    status=CheckStatus.SKIPPED,
                    confidence_delta=0.0,
                    reason="Skipped snippet check: file content unavailable.",
                ),
                {},
            )

        lines = file_content.splitlines()
        start_idx = max(0, line_range.start_line - 1)
        end_idx = min(len(lines), line_range.end_line)
        actual_slice = "\n".join(lines[start_idx:end_idx]).strip()

        claimed = (candidate.source_evidence or "").strip()

        if not claimed:
            return (
                ValidationCheckResult(
                    check_name="source_snippet_validation",
                    status=CheckStatus.WARNING,
                    confidence_delta=-0.15,
                    reason="No source code evidence provided by proposing agent.",
                    details={"extracted_code": actual_slice},
                ),
                {"extracted_code": actual_slice},
            )

        # 1. Exact or Whitespace-Trimmed Match
        if claimed in actual_slice or actual_slice in claimed:
            return (
                ValidationCheckResult(
                    check_name="source_snippet_validation",
                    status=CheckStatus.PASSED,
                    confidence_delta=+0.15,
                    reason="Exact source code match confirmed on target lines.",
                    details={"match_type": "exact", "extracted_code": actual_slice},
                ),
                {"extracted_code": actual_slice, "match_type": "exact"},
            )

        # 2. Token / Normalized Overlap
        claimed_tokens = set(re.findall(r"[A-Za-z0-9_]{3,}", claimed))
        actual_tokens = set(re.findall(r"[A-Za-z0-9_]{3,}", actual_slice))
        common_tokens = claimed_tokens & actual_tokens

        if claimed_tokens and len(common_tokens) / len(claimed_tokens) >= 0.6:
            return (
                ValidationCheckResult(
                    check_name="source_snippet_validation",
                    status=CheckStatus.PASSED,
                    confidence_delta=+0.08,
                    reason="Substantial token overlap matches target line context.",
                    details={"match_type": "token_overlap", "extracted_code": actual_slice},
                ),
                {"extracted_code": actual_slice, "match_type": "token_overlap"},
            )

        # 3. Line Drift Check (Code exists elsewhere in file)
        for idx, line in enumerate(lines):
            if claimed in line or any(t in line for t in claimed_tokens if len(t) > 6):
                drift_line = idx + 1
                return (
                    ValidationCheckResult(
                        check_name="source_snippet_validation",
                        status=CheckStatus.WARNING,
                        confidence_delta=-0.10,
                        reason=f"Line drift detected: Claimed snippet appears on line {drift_line} instead of lines [{line_range.start_line}, {line_range.end_line}].",
                        details={"drift_line": drift_line, "extracted_code": actual_slice},
                    ),
                    {"extracted_code": actual_slice, "drift_line": drift_line},
                )

        # 4. Fabricated / Completely Missing Snippet
        return (
            ValidationCheckResult(
                check_name="source_snippet_validation",
                status=CheckStatus.FAILED,
                confidence_delta=-0.60,
                reason=f"Claimed code snippet does not exist on lines [{line_range.start_line}, {line_range.end_line}] or elsewhere in file.",
                details={"actual_code": actual_slice, "claimed_code": claimed},
            ),
            {"extracted_code": actual_slice},
        )

    def _check_surrounding_code(
        self,
        candidate: CandidateFinding,
        file_content: Optional[str],
        line_range: LineRange,
    ) -> Tuple[ValidationCheckResult, bool]:
        """Check 4: Inspects enclosing function/scope for defensive guards that make the finding a false positive."""
        if file_content is None:
            return (
                ValidationCheckResult(
                    check_name="surrounding_code_analysis",
                    status=CheckStatus.SKIPPED,
                    confidence_delta=0.0,
                    reason="Surrounding code analysis skipped: file content unavailable.",
                ),
                False,
            )

        lines = file_content.splitlines()

        # Scope search to enclosing function/method to avoid bleeding into adjacent functions
        if not lines:
            target_line_idx = 0
        else:
            target_line_idx = min(len(lines) - 1, max(0, line_range.start_line - 1))

        start_idx = target_line_idx
        while start_idx > 0 and not lines[start_idx].lstrip().startswith(("def ", "async def ", "class ")):
            start_idx -= 1

        end_idx = min(len(lines), line_range.end_line)
        while end_idx < len(lines):
            line_str = lines[end_idx]
            if line_str.lstrip().startswith(("def ", "async def ", "class ")) and end_idx > line_range.end_line:
                break
            end_idx += 1

        surrounding_lines = lines[start_idx:end_idx]
        surrounding_text = "\n".join(surrounding_lines)

        issue_desc = (candidate.description + " " + candidate.title).lower()
        snippet_tokens = set(re.findall(r"[A-Za-z0-9_]+", candidate.source_evidence or ""))

        # Mitigations by Category / Issue Type
        # 1. Null / NoneType Protection
        if "none" in issue_desc or "null" in issue_desc or "undefined" in issue_desc:
            null_guards = [
                r"if\s+[\w_]+\s+is\s+not\s+None:",
                r"if\s+not\s+[\w_]+:\s*(?:return|raise|continue)",
                r"if\s*\([\w_]+\s*!=\s*null\)",
                r"if\s*\(![\w_]+\)\s*return",
                r"[\w_]+\?\.",
                r"[\w_]+\s*\?\?",
                r"Optional\[",
            ]
            for pattern in null_guards:
                match = re.search(pattern, surrounding_text)
                if match:
                    return (
                        ValidationCheckResult(
                            check_name="surrounding_code_analysis",
                            status=CheckStatus.FAILED,
                            confidence_delta=-0.65,
                            reason=f"False positive: Null/None issue is mitigated by surrounding guard: '{match.group(0)}'.",
                            details={"mitigation_pattern": pattern, "matched": match.group(0)},
                        ),
                        True,
                    )

        # 2. Exception / Error Handling Protection
        if "exception" in issue_desc or "crash" in issue_desc or "unhandled" in issue_desc:
            if "try:" in surrounding_text and "except" in surrounding_text:
                return (
                    ValidationCheckResult(
                        check_name="surrounding_code_analysis",
                        status=CheckStatus.FAILED,
                        confidence_delta=-0.60,
                        reason="False positive: Operation is wrapped in try/except block in surrounding scope.",
                    ),
                    True,
                )

        # 3. Input Validation & Sanitization Protection
        if "injection" in issue_desc or "sanitize" in issue_desc or "untrusted" in issue_desc or "traversal" in issue_desc:
            sanitizers = [
                r"os\.path\.basename\(",
                r"sanitize_\w+\(",
                r"validate_\w+\(",
                r"escape_\w+\(",
                r"html\.escape\(",
                r"shlex\.quote\(",
                r"re\.sub\(",
                r"int\(\w+\)",
                r"float\(\w+\)",
            ]
            for pat in sanitizers:
                match = re.search(pat, surrounding_text)
                if match:
                    # Check if the sanitized variable is relevant to the snippet
                    matched_call = match.group(0)
                    var_match = re.search(r"\((\w+)\)", matched_call)
                    if not var_match or not snippet_tokens or var_match.group(1) in snippet_tokens:
                        return (
                            ValidationCheckResult(
                                check_name="surrounding_code_analysis",
                                status=CheckStatus.FAILED,
                                confidence_delta=-0.60,
                                reason=f"False positive: Input is sanitized by upstream guard '{matched_call}'.",
                            ),
                            True,
                        )

        # 4. Concurrency & Lock Protection
        if "race condition" in issue_desc or "thread" in issue_desc:
            if "with lock:" in surrounding_text or "async with" in surrounding_text or "mutex" in surrounding_text:
                return (
                    ValidationCheckResult(
                        check_name="surrounding_code_analysis",
                        status=CheckStatus.FAILED,
                        confidence_delta=-0.55,
                        reason="False positive: Concurrency race condition mitigated by synchronization lock in surrounding block.",
                    ),
                    True,
                )

        # 5. Explicit Suppression Directive
        for line in surrounding_lines:
            if "# noqa" in line or "# type: ignore" in line or "// @ts-ignore" in line:
                return (
                    ValidationCheckResult(
                        check_name="surrounding_code_analysis",
                        status=CheckStatus.FAILED,
                        confidence_delta=-0.50,
                        reason=f"False positive: Explicit suppression directive detected: '{line.strip()}'.",
                    ),
                    True,
                )

        return (
            ValidationCheckResult(
                check_name="surrounding_code_analysis",
                status=CheckStatus.PASSED,
                confidence_delta=+0.10,
                reason="Surrounding code analysis found no mitigating guards or suppressions.",
            ),
            False,
        )

    def _check_repository_context(
        self,
        candidate: CandidateFinding,
        file_path: str,
        context_evidence: Optional[Dict[str, Any]],
    ) -> ValidationCheckResult:
        """Check 5: Evaluates architectural reachability, caller contracts, and import context."""
        if not context_evidence:
            return ValidationCheckResult(
                check_name="repository_context_validation",
                status=CheckStatus.SKIPPED,
                confidence_delta=0.0,
                reason="Repository context skipped: No AST context evidence provided.",
            )

        callers = context_evidence.get("callers", [])
        if callers:
            return ValidationCheckResult(
                check_name="repository_context_validation",
                status=CheckStatus.PASSED,
                confidence_delta=+0.08,
                reason=f"Callers verified in repository graph ({len(callers)} caller references found).",
                details={"caller_count": len(callers)},
            )

        return ValidationCheckResult(
            check_name="repository_context_validation",
            status=CheckStatus.PASSED,
            confidence_delta=+0.02,
            reason="Repository context validated without external conflicts.",
        )

    def _check_static_analysis(
        self,
        candidate: CandidateFinding,
        file_content: Optional[str],
        file_path: str,
    ) -> ValidationCheckResult:
        """Check 6: Performs AST parsing and static anti-pattern pattern verification."""
        if not file_content:
            return ValidationCheckResult(
                check_name="static_analysis",
                status=CheckStatus.SKIPPED,
                confidence_delta=0.0,
                reason="Static analysis skipped: File content unavailable.",
            )

        # If Python, attempt AST parse
        if file_path.endswith(".py"):
            try:
                ast.parse(file_content)
            except SyntaxError as e:
                return ValidationCheckResult(
                    check_name="static_analysis",
                    status=CheckStatus.WARNING,
                    confidence_delta=-0.10,
                    reason=f"File contains Python syntax error on line {e.lineno}: {e.msg}.",
                )

        # Scan for dangerous patterns confirmed by static inspection
        evidence_str = (candidate.source_evidence or "") + "\n" + file_content
        desc_lower = (candidate.description + " " + candidate.title).lower()

        # SQL Injection
        if "sql injection" in desc_lower or "sqli" in desc_lower:
            sqli_patterns = [
                r"f[\"'].*?SELECT.*?\{.*?\}",
                r"f[\"'].*?INSERT.*?\{.*?\}",
                r"f[\"'].*?UPDATE.*?\{.*?\}",
                r"f[\"'].*?DELETE.*?\{.*?\}",
                r"\.execute\s*\(\s*f[\"']",
                r"\.execute\s*\(\s*[\"'].*?%\s*",
            ]
            for pat in sqli_patterns:
                if re.search(pat, evidence_str, re.IGNORECASE):
                    return ValidationCheckResult(
                        check_name="static_analysis",
                        status=CheckStatus.PASSED,
                        confidence_delta=+0.15,
                        reason="Static analysis confirmed unparameterized SQL interpolation pattern in code.",
                        details={"rule": "SEC-SQLI-001"},
                    )

        # Command Injection
        if "command injection" in desc_lower or "rce" in desc_lower:
            cmd_patterns = [r"os\.system\(", r"shell=True", r"subprocess\.call\([^)]*shell=True"]
            for pat in cmd_patterns:
                if re.search(pat, evidence_str):
                    return ValidationCheckResult(
                        check_name="static_analysis",
                        status=CheckStatus.PASSED,
                        confidence_delta=+0.15,
                        reason="Static analysis confirmed dangerous command execution with shell=True or os.system.",
                        details={"rule": "SEC-CMD-001"},
                    )

        # Hardcoded Secrets
        if "secret" in desc_lower or "credential" in desc_lower or "api_key" in desc_lower:
            secret_pattern = r"(?i)(api_key|secret|password|token)\s*=\s*['\"][A-Za-z0-9+/=_-]{20,}['\"]"
            if re.search(secret_pattern, evidence_str):
                return ValidationCheckResult(
                    check_name="static_analysis",
                    status=CheckStatus.PASSED,
                    confidence_delta=+0.15,
                    reason="Static analysis confirmed hardcoded secret token assignment.",
                    details={"rule": "SEC-SECRET-001"},
                )

        return ValidationCheckResult(
            check_name="static_analysis",
            status=CheckStatus.PASSED,
            confidence_delta=+0.05,
            reason="Static syntax analysis passed without fatal anti-pattern contradictions.",
        )

    def _check_type_annotations(
        self,
        candidate: CandidateFinding,
        file_content: Optional[str],
        file_path: str,
    ) -> ValidationCheckResult:
        """Check 7: Inspects type annotations to verify if an alleged type flaw is possible."""
        if not file_content:
            return ValidationCheckResult(
                check_name="type_checking",
                status=CheckStatus.SKIPPED,
                confidence_delta=0.0,
                reason="Type checking skipped: No file content available.",
            )

        desc = (candidate.description + " " + candidate.title).lower()

        # If agent claims variable might be None, inspect type annotations
        if "none" in desc or "null" in desc:
            # Check for non-Optional primitive annotations like `name: str` or `count: int = 0`
            match = re.search(r"(\w+)\s*:\s*(int|str|bool|float|dict|list)\s*(?:=|,|\))", file_content)
            if match and match.group(1) in desc:
                var_name = match.group(1)
                t_name = match.group(2)
                return ValidationCheckResult(
                    check_name="type_checking",
                    status=CheckStatus.FAILED,
                    confidence_delta=-0.30,
                    reason=f"Type signature contradicts claim: '{var_name}' is statically annotated as non-nullable '{t_name}'.",
                )

        return ValidationCheckResult(
            check_name="type_checking",
            status=CheckStatus.PASSED,
            confidence_delta=+0.05,
            reason="Type check passed: No static type annotation contradictions found.",
        )

    def _check_test_reproduction(
        self,
        candidate: CandidateFinding,
        file_path: str,
        test_files: Optional[List[str]],
    ) -> ValidationCheckResult:
        """Check 8: Checks whether test suites exist to reproduce or assert the defect."""
        if not test_files:
            return ValidationCheckResult(
                check_name="test_reproduction",
                status=CheckStatus.SKIPPED,
                confidence_delta=0.0,
                reason="Test reproduction skipped: No test catalog provided.",
            )

        base_name = os.path.basename(file_path).split(".")[0]
        matching_tests = [t for t in test_files if base_name in t or f"test_{base_name}" in t]

        if matching_tests:
            return ValidationCheckResult(
                check_name="test_reproduction",
                status=CheckStatus.PASSED,
                confidence_delta=+0.08,
                reason=f"Unit test suite identified for target module: {matching_tests[0]}.",
                details={"matching_tests": matching_tests},
            )

        return ValidationCheckResult(
            check_name="test_reproduction",
            status=CheckStatus.PASSED,
            confidence_delta=0.0,
            reason="No existing unit test directly references the modified unit.",
        )

    def _check_duplicates(
        self,
        candidate: CandidateFinding,
        line_range: LineRange,
        existing_findings: Optional[List[VerifiedFinding]],
    ) -> Tuple[ValidationCheckResult, Optional[str]]:
        """Check 9: Detects redundant overlapping findings across agents and batches."""
        if not existing_findings:
            return (
                ValidationCheckResult(
                    check_name="duplicate_detection",
                    status=CheckStatus.PASSED,
                    confidence_delta=0.0,
                    reason="No duplicate findings detected.",
                ),
                None,
            )

        cand_title_words = set(re.findall(r"[A-Za-z0-9]{4,}", candidate.title.lower()))
        norm_path = candidate.file_path.replace("\\", "/").strip("/")

        for prev in existing_findings:
            if prev.file_path != norm_path:
                continue

            # Overlapping line bounds (tolerance 3 lines)
            if line_range.overlaps(prev.line_range, tolerance=3):
                # Check category or title keyword overlap
                prev_title_words = set(re.findall(r"[A-Za-z0-9]{4,}", prev.title.lower()))
                common_words = cand_title_words & prev_title_words

                if prev.category == candidate.category or len(common_words) >= 2:
                    return (
                        ValidationCheckResult(
                            check_name="duplicate_detection",
                            status=CheckStatus.FAILED,
                            confidence_delta=-0.80,
                            reason=f"Duplicate detected: Overlaps with primary finding #{prev.id} ('{prev.title}') at lines [{prev.line_range.start_line}, {prev.line_range.end_line}].",
                            details={"duplicate_of_id": prev.id},
                        ),
                        prev.id,
                    )

        return (
            ValidationCheckResult(
                check_name="duplicate_detection",
                status=CheckStatus.PASSED,
                confidence_delta=0.0,
                reason="Finding is distinct and non-redundant.",
            ),
            None,
        )

    def _check_severity_assessment(
        self,
        candidate: CandidateFinding,
    ) -> Tuple[ValidationCheckResult, FindingSeverity]:
        """Check 10: Validates and normalizes severity based on objective risk rules."""
        raw_sev = FindingSeverity.from_str(candidate.severity)
        text = (candidate.title + " " + candidate.description).lower()

        # Defend against severity inflation for cosmetic issues
        if re.search(r"\b(typo|formatting style|code format|indentation|style guide|docstring)\b", text):
            assessed = FindingSeverity.INFORMATIONAL
        # Ensure severe security vulnerabilities are at least Critical
        elif any(w in text for w in ("rce", "remote code execution", "sql injection", "auth bypass", "hardcoded secret")):
            assessed = FindingSeverity.CRITICAL
        else:
            assessed = raw_sev

        if assessed != raw_sev:
            return (
                ValidationCheckResult(
                    check_name="severity_assessment",
                    status=CheckStatus.WARNING,
                    confidence_delta=+0.02,
                    reason=f"Calibrated severity from '{raw_sev.value}' to objective level '{assessed.value}'.",
                ),
                assessed,
            )

        return (
            ValidationCheckResult(
                check_name="severity_assessment",
                status=CheckStatus.PASSED,
                confidence_delta=+0.02,
                reason=f"Assessed severity '{assessed.value}' verified against objective risk classification.",
            ),
            assessed,
        )

    def _calibrate_confidence(
        self,
        candidate: CandidateFinding,
        checks: List[ValidationCheckResult],
        is_fatal: bool,
        is_false_positive: bool,
        duplicate_of_id: Optional[str],
    ) -> Tuple[ValidationCheckResult, float, VerificationStatus]:
        """Check 11: Calibrates numerical confidence strictly separate from severity."""
        base_confidence = candidate.confidence if candidate.confidence is not None else 0.75
        delta_sum = sum(c.confidence_delta for c in checks)

        calibrated = base_confidence + delta_sum

        # Hard constraints for fatal failures
        if is_fatal:
            calibrated = min(calibrated, 0.10)
            status = VerificationStatus.REJECTED
        elif is_false_positive:
            calibrated = min(calibrated, 0.25)
            status = VerificationStatus.REJECTED
        elif duplicate_of_id:
            calibrated = min(calibrated, 0.20)
            status = VerificationStatus.REJECTED
        else:
            if calibrated >= 0.85:
                status = VerificationStatus.CONFIRMED
            elif calibrated >= 0.70:
                status = VerificationStatus.HIGH_CONFIDENCE
            elif calibrated >= 0.40:
                status = VerificationStatus.NEEDS_INVESTIGATION
            else:
                status = VerificationStatus.REJECTED

        # Ensure calibrated confidence is strictly bounded within [0.0, 1.0]
        calibrated = max(0.0, min(1.0, round(calibrated, 2)))

        return (
            ValidationCheckResult(
                check_name="confidence_calibration",
                status=CheckStatus.PASSED,
                confidence_delta=0.0,
                reason=f"Calibrated confidence to {calibrated:.2f} resulting in status '{status.value}' (independent of severity).",
                details={"calibrated_confidence": calibrated, "status": status.value},
            ),
            calibrated,
            status,
        )

    def _check_actionability(
        self,
        candidate: CandidateFinding,
        line_range: LineRange,
    ) -> Tuple[ValidationCheckResult, float]:
        """Check 12: Evaluates actionability score (root cause, impact, remediation, line precision)."""
        score = 0.0

        # Root cause (+0.25)
        if candidate.root_cause and len(candidate.root_cause.strip()) >= 10:
            score += 0.25

        # Impact statement (+0.25)
        if candidate.impact and len(candidate.impact.strip()) >= 10:
            score += 0.25

        # Suggested remediation (+0.30)
        if candidate.suggested_remediation and len(candidate.suggested_remediation.strip()) >= 15:
            score += 0.30

        # Line range specificity (+0.20)
        span = line_range.end_line - line_range.start_line
        if 0 <= span <= 25:
            score += 0.20

        score = round(score, 2)

        status = CheckStatus.PASSED if score >= 0.60 else CheckStatus.WARNING
        return (
            ValidationCheckResult(
                check_name="actionability_assessment",
                status=status,
                confidence_delta=0.0,
                reason=f"Actionability scored at {score:.2f}/1.0 (Root cause: {'yes' if candidate.root_cause else 'no'}, Remediation: {'yes' if candidate.suggested_remediation else 'no'}).",
                details={"actionability_score": score},
            ),
            score,
        )

    # -------------------------------------------------------------------------
    # Inference Helpers for Missing Metadata
    # -------------------------------------------------------------------------

    def _infer_root_cause(self, candidate: CandidateFinding) -> str:
        """Derives a technical root cause if not explicitly provided."""
        t = candidate.title.lower()
        if "sql injection" in t:
            return "Unsanitized user-controlled parameter directly interpolated into SQL query text."
        if "none" in t or "null" in t:
            return "Dereferencing potentially null object without upstream existence validation."
        if "memory" in t or "leak" in t:
            return "Unbounded growth of collection across long-lived process execution."
        if "injection" in t:
            return "Passing untrusted input directly to operating system execution shell."
        return f"Defect in {candidate.file_path}: {candidate.title}."

    def _infer_impact(self, candidate: CandidateFinding, severity: FindingSeverity) -> str:
        """Derives an impact statement based on severity."""
        if severity == FindingSeverity.CRITICAL:
            return "Critical exposure: Potential for arbitrary code execution, database compromise, or unauthorized data exfiltration."
        elif severity == FindingSeverity.HIGH:
            return "High impact: Security degradation, service instability, or persistent memory leakage."
        elif severity == FindingSeverity.MEDIUM:
            return "Medium impact: Unhandled exceptions under edge-case conditions, performance degradation under concurrency."
        elif severity == FindingSeverity.LOW:
            return "Low impact: Code smell, maintenance friction, or sub-optimal resource utilization."
        return "Informational note: Stylistic inconsistency or minor documentation gap."
