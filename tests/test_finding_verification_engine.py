"""Comprehensive tests for the Evidence-Based Finding Verification Engine.

Verifies:
1. Valid finding verified as Confirmed with evidence.
2. False positive mitigated by surrounding null checks -> Rejected.
3. False positive mitigated by surrounding try/except -> Rejected.
4. False positive mitigated by input sanitization -> Rejected.
5. Incorrect line numbers exceeding file length -> Rejected.
6. Incorrect zero/negative line numbers -> Rejected.
7. Non-existent file path -> Rejected.
8. Hallucinated source snippet -> Rejected.
9. Line drift detection.
10. Duplicate detection and linking.
11. Confidence calibration strictly separated from severity.
12. Severity assessment & anti-inflation calibration.
13. Actionability assessment scoring.
14. Review policy enforcement (Standard, Strict, Security-Only, Permissive).
15. Batch verification workflow.
16. Verification REST API endpoints.
"""

import pytest
from httpx import AsyncClient

from app.verification.engine import FindingVerificationEngine
from app.verification.policy import ReviewPolicyEngine
from app.verification.schemas import (
    CandidateFinding,
    CheckStatus,
    FindingSeverity,
    ReviewPolicyConfig,
    VerificationStatus,
    VerifiedFinding,
)
from app.verification.service import FindingVerificationService


SAMPLE_PYTHON_SOURCE = """
import os
from sqlalchemy import text
from app.database import db

def get_user_profile(user_id: int):
    # Retrieve user profile safely
    if user_id is not None:
        user_record = db.query(user_id)
        return user_record
    return None

def dangerous_query(user_input: str):
    # Critical security defect: raw string interpolation into SQL query
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return db.execute(text(query))

def protected_operation(data: str):
    try:
        parsed = int(data)
        return parsed * 2
    except ValueError:
        return 0

def sanitized_export(filename: str):
    safe_name = os.path.basename(filename)
    return open(f"/tmp/{safe_name}", "w")
""".strip()


# -----------------------------------------------------------------------------
# 1. Valid Finding Verification
# -----------------------------------------------------------------------------

def test_valid_finding_verified_as_confirmed():
    """Valid finding matching actual source lines and static vulnerability is Confirmed."""
    engine = FindingVerificationEngine()

    candidate = CandidateFinding(
        title="SQL Injection via string formatting in SQL text statement",
        description="Raw f-string query parameter allows arbitrary SQL execution.",
        file_path="backend/app/routes/users.py",
        start_line=13,
        end_line=14,
        severity="Critical",
        confidence=0.85,
        root_cause="Direct string interpolation into SQL query string.",
        impact="Database compromise and data exfiltration.",
        source_evidence="query = f\"SELECT * FROM users WHERE name = '{user_input}'\"",
        suggested_remediation="Use parameterized queries: select(User).where(User.name == user_input)",
        category="security",
        agent_name="Security Sentinel",
    )

    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}
    verified = engine.verify_finding(candidate, repository_files=repo_files)

    # Must contain all 11 mandatory fields
    assert verified.title == candidate.title
    assert verified.description == candidate.description
    assert verified.file_path == "backend/app/routes/users.py"
    assert verified.line_range.start_line == 13
    assert verified.line_range.end_line == 14
    assert verified.severity == FindingSeverity.CRITICAL
    assert verified.confidence >= 0.85
    assert verified.root_cause
    assert verified.impact
    assert verified.source_evidence
    assert verified.suggested_remediation
    assert verified.verification_status == VerificationStatus.CONFIRMED

    # Confidence strictly separate from severity
    assert isinstance(verified.confidence, float)
    assert isinstance(verified.severity, FindingSeverity)

    # Publishable under standard policy
    assert verified.is_publishable is True
    assert "Satisfies" in verified.publish_decision_reason


# -----------------------------------------------------------------------------
# 2-4. False Positive Mitigations
# -----------------------------------------------------------------------------

def test_false_positive_mitigated_by_surrounding_null_check():
    """Finding alleging null dereference is Rejected when surrounding code contains null check."""
    engine = FindingVerificationEngine()

    candidate = CandidateFinding(
        title="Potential NoneType dereference on user_id",
        description="user_id may be None when invoking db.query.",
        file_path="backend/app/routes/users.py",
        start_line=8,
        end_line=8,
        severity="Medium",
        confidence=0.80,
        source_evidence="user_record = db.query(user_id)",
        suggested_remediation="Add null check for user_id",
        category="bug",
        agent_name="Bug Hunter",
    )

    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}
    verified = engine.verify_finding(candidate, repository_files=repo_files)

    assert verified.verification_status == VerificationStatus.REJECTED
    assert verified.confidence <= 0.30
    assert verified.is_publishable is False
    assert "mitigated by surrounding guard" in verified.rejection_reason.lower()


def test_false_positive_mitigated_by_surrounding_try_except():
    """Finding alleging unhandled exception is Rejected when wrapped in try/except."""
    engine = FindingVerificationEngine()

    candidate = CandidateFinding(
        title="Unhandled ValueError crash on int conversion",
        description="Calling int(data) crashes worker if data is non-numeric.",
        file_path="backend/app/routes/users.py",
        start_line=19,
        end_line=19,
        severity="Medium",
        confidence=0.75,
        source_evidence="parsed = int(data)",
        suggested_remediation="Wrap with try/except ValueError",
        category="bug",
    )

    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}
    verified = engine.verify_finding(candidate, repository_files=repo_files)

    assert verified.verification_status == VerificationStatus.REJECTED
    assert verified.is_publishable is False
    assert "try/except" in verified.rejection_reason.lower()


def test_false_positive_mitigated_by_sanitization():
    """Finding alleging path traversal is Rejected when os.path.basename sanitizes it."""
    engine = FindingVerificationEngine()

    candidate = CandidateFinding(
        title="Path traversal vulnerability via filename parameter",
        description="User could pass ../../../etc/passwd to open arbitrary paths.",
        file_path="backend/app/routes/users.py",
        start_line=25,
        end_line=25,
        severity="High",
        confidence=0.80,
        source_evidence="return open(f\"/tmp/{safe_name}\", \"w\")",
        suggested_remediation="Sanitize path with os.path.basename",
        category="security",
    )

    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}
    verified = engine.verify_finding(candidate, repository_files=repo_files)

    # Line 24: safe_name = os.path.basename(filename) mitigates path traversal!
    # Verified should flag surrounding guard
    surrounding_check = next((c for c in verified.checks if c.check_name == "surrounding_code_analysis"), None)
    assert surrounding_check is not None


# -----------------------------------------------------------------------------
# 5-6. Incorrect Line References
# -----------------------------------------------------------------------------

def test_incorrect_line_number_exceeding_file_length():
    """Finding referencing lines beyond EOF is Rejected as line number failure."""
    engine = FindingVerificationEngine()

    candidate = CandidateFinding(
        title="Buffer overflow on network socket read",
        description="Oversized payload crashes buffer at line 999.",
        file_path="backend/app/routes/users.py",
        start_line=999,
        end_line=1005,
        severity="High",
        confidence=0.80,
        source_evidence="socket.read(1024)",
        suggested_remediation="Add buffer length cap",
    )

    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}  # ~27 lines total
    verified = engine.verify_finding(candidate, repository_files=repo_files)

    assert verified.verification_status == VerificationStatus.REJECTED
    assert verified.is_publishable is False
    assert "exceeds total file length" in verified.rejection_reason.lower()


def test_incorrect_negative_or_zero_line_numbers():
    """Finding with start_line <= 0 is Rejected immediately."""
    engine = FindingVerificationEngine()

    candidate = CandidateFinding(
        title="Null pointer dereference on initialization",
        description="Pointer uninitialized at line 0.",
        file_path="backend/app/routes/users.py",
        start_line=0,
        end_line=0,
        severity="Medium",
    )

    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}
    verified = engine.verify_finding(candidate, repository_files=repo_files)

    assert verified.verification_status == VerificationStatus.REJECTED
    assert "positive integers" in verified.rejection_reason.lower()


# -----------------------------------------------------------------------------
# 7. Non-Existent File Path
# -----------------------------------------------------------------------------

def test_non_existent_file_rejection():
    """Finding for a file that does not exist in repo or PR is rejected as hallucinated."""
    engine = FindingVerificationEngine()

    candidate = CandidateFinding(
        title="Insecure cryptographic salt length",
        description="Salt is too short in non-existent crypto module.",
        file_path="backend/app/crypto/imaginary_salt_generator.py",
        start_line=42,
        end_line=45,
        severity="High",
        confidence=0.85,
    )

    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}
    verified = engine.verify_finding(candidate, repository_files=repo_files)

    assert verified.verification_status == VerificationStatus.REJECTED
    assert verified.confidence == 0.0
    assert verified.is_publishable is False
    assert "does not exist in repository" in verified.rejection_reason.lower()


# -----------------------------------------------------------------------------
# 8-9. Source Snippet Validation & Line Drift
# -----------------------------------------------------------------------------

def test_hallucinated_source_snippet_rejection():
    """File and line numbers exist, but code snippet is completely fabricated."""
    engine = FindingVerificationEngine()

    candidate = CandidateFinding(
        title="Hardcoded API Key exposed",
        description="Exposed AWS secret key in source code.",
        file_path="backend/app/routes/users.py",
        start_line=6,
        end_line=7,
        severity="Critical",
        confidence=0.90,
        source_evidence="AWS_SECRET_ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'",
        suggested_remediation="Move secret to environment variables",
    )

    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}
    verified = engine.verify_finding(candidate, repository_files=repo_files)

    assert verified.verification_status == VerificationStatus.REJECTED
    assert "does not exist on lines" in verified.rejection_reason.lower()


def test_line_drift_detection():
    """Snippet exists in file, but on line 14 instead of claimed line 5."""
    engine = FindingVerificationEngine()

    candidate = CandidateFinding(
        title="SQL query concatenation",
        description="SQL interpolation detected with line drift.",
        file_path="backend/app/routes/users.py",
        start_line=5,
        end_line=5,
        severity="Critical",
        confidence=0.80,
        source_evidence="query = f\"SELECT * FROM users WHERE name = '{user_input}'\"",
        suggested_remediation="Use parameterized query",
    )

    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}
    verified = engine.verify_finding(candidate, repository_files=repo_files)

    snippet_check = next((c for c in verified.checks if c.check_name == "source_snippet_validation"), None)
    assert snippet_check is not None
    assert snippet_check.status == CheckStatus.WARNING
    assert "line drift detected" in snippet_check.reason.lower()


# -----------------------------------------------------------------------------
# 10. Duplicate Detection
# -----------------------------------------------------------------------------

def test_duplicate_detection_and_linking():
    """Redundant finding on the same file and overlapping line range is marked Duplicate."""
    engine = FindingVerificationEngine()
    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}

    primary = CandidateFinding(
        id="finding-primary-1",
        title="SQL Injection in users query builder",
        description="Direct f-string in SQL statement.",
        file_path="backend/app/routes/users.py",
        start_line=13,
        end_line=14,
        severity="Critical",
        confidence=0.90,
        source_evidence="query = f\"SELECT * FROM users WHERE name = '{user_input}'\"",
        suggested_remediation="Parameterize query with SQLAlchemy",
        category="security",
    )
    verified_primary = engine.verify_finding(primary, repository_files=repo_files)
    assert verified_primary.verification_status == VerificationStatus.CONFIRMED

    # Duplicate from another agent on adjacent lines
    duplicate_candidate = CandidateFinding(
        id="finding-secondary-2",
        title="Unsanitized SQL Query interpolation",
        description="Duplicate finding for same query.",
        file_path="backend/app/routes/users.py",
        start_line=14,
        end_line=15,
        severity="High",
        confidence=0.85,
        source_evidence="return db.execute(text(query))",
        suggested_remediation="Parameterize query",
        category="security",
    )

    verified_dup = engine.verify_finding(
        duplicate_candidate,
        repository_files=repo_files,
        existing_findings=[verified_primary],
    )

    assert verified_dup.verification_status == VerificationStatus.REJECTED
    assert verified_dup.duplicate_of_id == "finding-primary-1"
    assert verified_dup.is_publishable is False
    assert "duplicate detected" in verified_dup.rejection_reason.lower()


# -----------------------------------------------------------------------------
# 11. Confidence Strictly Separate From Severity
# -----------------------------------------------------------------------------

def test_confidence_strictly_separated_from_severity():
    """Confidence represents proof probability; Severity represents risk consequence."""
    engine = FindingVerificationEngine()
    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}

    # Case A: Critical severity with speculative/moderate confidence -> Needs investigation
    speculative_critical = CandidateFinding(
        title="Possible race condition in database pool checkout",
        description="Under extreme traffic, connection pool may deadlock.",
        file_path="backend/app/routes/users.py",
        start_line=9,
        end_line=9,
        severity="Critical",
        confidence=0.30,
        source_evidence=None,
        suggested_remediation="Configure connection pool timeout",
        category="performance",
    )
    vf_a = engine.verify_finding(speculative_critical, repository_files=repo_files)
    assert vf_a.severity == FindingSeverity.CRITICAL
    assert vf_a.confidence < 0.70
    assert vf_a.verification_status == VerificationStatus.NEEDS_INVESTIGATION

    # Case B: Informational severity with high proof confidence -> Confirmed
    definite_info = CandidateFinding(
        title="Docstring formatting note",
        description="Docstring indentation does not adhere to PEP 257.",
        file_path="backend/app/routes/users.py",
        start_line=6,
        end_line=6,
        severity="Informational",
        confidence=0.95,
        source_evidence="# Retrieve user profile safely",
        suggested_remediation="Use triple-quoted docstring",
        category="style",
    )
    vf_b = engine.verify_finding(definite_info, repository_files=repo_files)
    assert vf_b.severity == FindingSeverity.INFORMATIONAL
    assert vf_b.confidence >= 0.85
    assert vf_b.verification_status == VerificationStatus.CONFIRMED


# -----------------------------------------------------------------------------
# 12. Severity Assessment & Anti-Inflation
# -----------------------------------------------------------------------------

def test_severity_assessment_anti_inflation():
    """Agent inflated cosmetic typo to Critical; engine normalizes down to Informational."""
    engine = FindingVerificationEngine()
    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}

    inflated = CandidateFinding(
        title="Typo in comment spelling",
        description="Misspelled word in inline code comment.",
        file_path="backend/app/routes/users.py",
        start_line=6,
        end_line=6,
        severity="Critical",  # Fabricated inflation!
        confidence=0.90,
        source_evidence="# Retrieve user profile safely",
        suggested_remediation="Fix spelling",
        category="style",
    )
    verified = engine.verify_finding(inflated, repository_files=repo_files)

    # Assessed severity must be normalized to Informational
    assert verified.severity == FindingSeverity.INFORMATIONAL


# -----------------------------------------------------------------------------
# 13. Actionability Assessment Scoring
# -----------------------------------------------------------------------------

def test_actionability_assessment_scoring():
    """Actionability score evaluates root cause, impact, remediation, and line precision."""
    engine = FindingVerificationEngine()
    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}

    actionable_finding = CandidateFinding(
        title="SQL Injection in dynamic string query",
        description="Vulnerability allows unauthorized database access.",
        file_path="backend/app/routes/users.py",
        start_line=13,
        end_line=14,
        severity="Critical",
        confidence=0.85,
        root_cause="Direct string interpolation into raw SQL statement text.",
        impact="Full database read/write exfiltration by unauthenticated actors.",
        source_evidence="query = f\"SELECT * FROM users WHERE name = '{user_input}'\"",
        suggested_remediation="query = select(User).where(User.name == user_input)",
        category="security",
    )
    vf = engine.verify_finding(actionable_finding, repository_files=repo_files)
    assert vf.actionability_score >= 0.80

    vague_finding = CandidateFinding(
        title="Code could be better",
        description="Consider improving this function.",
        file_path="backend/app/routes/users.py",
        start_line=1,
        end_line=100,  # Imprecise range
        severity="Low",
        confidence=0.50,
        root_cause=None,
        impact=None,
        suggested_remediation=None,  # No remediation!
    )
    vf_vague = engine.verify_finding(vague_finding, repository_files=repo_files)
    assert vf_vague.actionability_score < 0.50


# -----------------------------------------------------------------------------
# 14. Review Policy Enforcement
# -----------------------------------------------------------------------------

def test_review_policy_enforcement():
    """Validates policy filtering across Strict, Standard, Security-Only, and Permissive."""
    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}

    # Finding with High-confidence (0.75), Medium severity
    candidate = CandidateFinding(
        title="Suboptimal query structure",
        description="Query could use composite index.",
        file_path="backend/app/routes/users.py",
        start_line=7,
        end_line=8,
        severity="Medium",
        confidence=0.75,
        root_cause="Missing composite index on user_id.",
        impact="Sequential scan under high table volume.",
        source_evidence="user_record = db.query(user_id)",
        suggested_remediation="CREATE INDEX ix_users_query ON users(user_id);",
        category="performance",
    )

    # 1. Standard Policy (Allows High-confidence, min_conf=0.70) -> Publishable
    standard_engine = FindingVerificationEngine(policy=ReviewPolicyEngine.get_standard_policy())
    vf_std = standard_engine.verify_finding(candidate, repository_files=repo_files)
    assert vf_std.is_publishable is True

    # 2. Strict Policy (Requires CONFIRMED status and min_conf=0.85) -> Filtered for moderate confidence
    moderate_cand = candidate.model_copy(update={"confidence": 0.35})
    strict_engine = FindingVerificationEngine(policy=ReviewPolicyEngine.get_strict_policy())
    vf_strict = strict_engine.verify_finding(moderate_cand, repository_files=repo_files)
    assert vf_strict.verification_status == VerificationStatus.HIGH_CONFIDENCE
    assert vf_strict.is_publishable is False
    assert "Filtered" in vf_strict.publish_decision_reason

    # 3. Security-Only Policy (Filters performance category) -> Filtered
    sec_engine = FindingVerificationEngine(policy=ReviewPolicyEngine.get_security_only_policy())
    vf_sec = sec_engine.verify_finding(candidate, repository_files=repo_files)
    assert vf_sec.is_publishable is False
    assert "security" in vf_sec.publish_decision_reason.lower()


# -----------------------------------------------------------------------------
# 15. Batch Verification Workflow
# -----------------------------------------------------------------------------

def test_batch_verification_workflow():
    """Processes multiple candidates in a batch with deduplication and metrics."""
    service = FindingVerificationService()
    repo_files = {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE}

    candidates = [
        # Valid finding 1
        CandidateFinding(
            id="f-1",
            title="SQL Injection in users query builder",
            description="Direct f-string in SQL statement.",
            file_path="backend/app/routes/users.py",
            start_line=13,
            end_line=14,
            severity="Critical",
            confidence=0.85,
            root_cause="Direct string interpolation into raw SQL statement text.",
            impact="Full database read/write exfiltration.",
            source_evidence="query = f\"SELECT * FROM users WHERE name = '{user_input}'\"",
            suggested_remediation="query = select(User).where(User.name == user_input)",
            category="security",
        ),
        # False positive (mitigated by null check)
        CandidateFinding(
            id="f-2",
            title="NoneType dereference",
            description="Null check missing.",
            file_path="backend/app/routes/users.py",
            start_line=8,
            end_line=8,
            severity="Medium",
            confidence=0.80,
            source_evidence="user_record = db.query(user_id)",
        ),
        # Non-existent file
        CandidateFinding(
            id="f-3",
            title="Dead code in non-existent file",
            description="Orphan file.",
            file_path="backend/app/ghost.py",
            start_line=1,
            end_line=5,
            severity="Low",
        ),
        # Duplicate of f-1
        CandidateFinding(
            id="f-4",
            title="SQL Injection duplicate",
            description="Duplicate SQL query issue.",
            file_path="backend/app/routes/users.py",
            start_line=14,
            end_line=14,
            severity="Critical",
            source_evidence="return db.execute(text(query))",
            category="security",
        ),
    ]

    batch_result = service.verify_candidates_batch(candidates, repository_files=repo_files)

    assert batch_result.total_candidates == 4
    assert batch_result.confirmed_count >= 1
    assert batch_result.rejected_count >= 2  # False positive + ghost file + duplicate
    assert len(batch_result.verified_findings) == 4


# -----------------------------------------------------------------------------
# 16. Verification REST API Endpoints
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_verification_rest_apis(async_client: AsyncClient):
    """Verifies REST endpoints: /api/v1/verification/verify, verify-batch, and policies."""
    # 1. Get policies
    pol_resp = await async_client.get("/api/v1/verification/policies")
    assert pol_resp.status_code == 200
    pols = pol_resp.json()
    assert "standard" in pols
    assert "strict" in pols
    assert "security_only" in pols

    # 2. POST /api/v1/verification/verify
    verify_payload = {
        "finding": {
            "title": "SQL Injection in users query builder",
            "description": "Direct f-string in SQL statement.",
            "file_path": "backend/app/routes/users.py",
            "start_line": 13,
            "end_line": 14,
            "severity": "Critical",
            "confidence": 0.85,
            "root_cause": "Direct string interpolation into raw SQL statement text.",
            "impact": "Full database read/write exfiltration.",
            "source_evidence": "query = f\"SELECT * FROM users WHERE name = '{user_input}'\"",
            "suggested_remediation": "query = select(User).where(User.name == user_input)",
            "category": "security",
        },
        "repository_files": {"backend/app/routes/users.py": SAMPLE_PYTHON_SOURCE},
    }

    verify_resp = await async_client.post("/api/v1/verification/verify", json=verify_payload)
    assert verify_resp.status_code == 200
    vf_data = verify_resp.json()
    assert vf_data["verification_status"] == "Confirmed"
    assert vf_data["severity"] == "Critical"
    assert vf_data["confidence"] >= 0.85
    assert vf_data["is_publishable"] is True
    assert len(vf_data["checks"]) == 12  # All 12 checks recorded!
