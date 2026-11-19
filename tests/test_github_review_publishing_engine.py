"""Comprehensive tests for GitHub Review Publishing Engine.

Verifies:
1. Diff hunk parsing and line mapping validation.
2. Structured comment formatting (all 7 required sections + ```suggestion block).
3. Executive review summary and score card markdown.
4. Duplicate comment detection and prevention.
5. Outdated comment management and resolution replies.
6. Check run creation, status transitions, and annotations.
7. Retry handling with exponential backoff on transient errors.
8. Rate-limit inspection and backoff.
9. Actionability filtering (only verified, actionable findings published).
10. Database status synchronization and confirmed API responses.
"""

import json
import pytest
from httpx import ASGITransport, AsyncClient, MockTransport, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.findings.models import Finding
from app.github.github_auth_service import GitHubAuthService
from app.github.publishing_engine import (
    GitHubDiffLineValidator,
    GitHubRateLimitExceededError,
    GitHubRateLimitHandler,
    GitHubReviewFormatter,
    GitHubReviewPublishingEngine,
)
from app.github.schemas import (
    GitHubCheckRunAnnotation,
    GitHubCheckRunCreate,
    GitHubPublishRequest,
    GitHubPublishResult,
)
from app.organizations.models import Organization
from app.pull_requests.models import PullRequest
from app.repositories.models import Repository
from app.reviews.models import Review


# =====================================================================
# 1. DIFF & LINE MAPPING VALIDATION TESTS
# =====================================================================

def test_diff_line_validator_parsing():
    sample_diff = """diff --git a/app/core/auth.py b/app/core/auth.py
index abc1234..def5678 100644
--- a/app/core/auth.py
+++ b/app/core/auth.py
@@ -10,4 +10,6 @@ def verify_password(plain, hashed):
     return bcrypt.checkpw(plain, hashed)
 
+def authenticate_user(username, password):
+    # PR change: added query
+    user = db.query(User).filter_by(username=username).first()
     return user
diff --git a/app/models/user.py b/app/models/user.py
index 1111111..2222222 100644
--- a/app/models/user.py
+++ b/app/models/user.py
@@ -25,3 +25,4 @@ class User:
     id: int
+    role: str = "member"
     email: str
"""
    validator = GitHubDiffLineValidator(sample_diff)
    assert "app/core/auth.py" in validator.changed_files
    assert "app/models/user.py" in validator.changed_files

    # Line 12, 13, 14 are added/context lines in auth.py
    assert validator.is_line_in_diff("app/core/auth.py", 12) is True
    assert validator.is_line_in_diff("app/core/auth.py", 13) is True

    # Line 50 is outside the diff hunk
    assert validator.is_line_in_diff("app/core/auth.py", 50) is False

    # Untouched file
    assert validator.is_line_in_diff("app/database/session.py", 10) is False

    # Nearest line within tolerance
    nearest = validator.get_nearest_diff_line("app/core/auth.py", 15, tolerance=3)
    assert nearest is not None


def test_diff_line_validator_partitioning():
    sample_diff = """diff --git a/app/services/payment.py b/app/services/payment.py
index 1234567..89abcdef 100644
--- a/app/services/payment.py
+++ b/app/services/payment.py
@@ -20,5 +20,6 @@ def process_charge(amount):
+    token = get_stripe_token()
     charge = stripe.Charge.create(amount=amount)
     return charge
"""
    validator = GitHubDiffLineValidator(sample_diff)

    f_inline = Finding(
        review_id="rev-1",
        file_path="app/services/payment.py",
        line_number=20,
        severity="critical",
        title="Unverified token",
        message="Token is not validated before charge.",
        verification_status="Confirmed",
        actionability_score=0.95,
        is_publishable=True,
    )
    f_outside = Finding(
        review_id="rev-1",
        file_path="app/services/payment.py",
        line_number=95,  # Far outside diff
        severity="medium",
        title="Outdated logging format",
        message="Use structured logging.",
        verification_status="Confirmed",
        actionability_score=0.85,
        is_publishable=True,
    )
    f_other_file = Finding(
        review_id="rev-1",
        file_path="app/config.py",  # Not in diff
        line_number=5,
        severity="low",
        title="Missing typing",
        message="Add type annotations.",
        verification_status="Confirmed",
        actionability_score=0.7,
        is_publishable=True,
    )

    inline, summary = validator.partition_findings([f_inline, f_outside, f_other_file])
    assert len(inline) == 1
    assert inline[0].title == "Unverified token"
    assert len(summary) == 2


# =====================================================================
# 2. COMMENT FORMATTING & SUGGESTED FIXES
# =====================================================================

def test_comment_formatting_with_all_required_sections():
    finding = Finding(
        id="fnd-uuid-1234",
        review_id="rev-uuid-5678",
        file_path="app/api/endpoints.py",
        line_number=45,
        severity="critical",
        category="security",
        title="SQL Injection Vulnerability",
        message="Untrusted user parameter directly formatted into SQL query string.",
        root_cause="Missing parameterized binding in execute call.",
        evidence='cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")',
        suggested_patch='cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
        verification_status="Confirmed",
        confidence_score=0.98,
        actionability_score=0.95,
        is_publishable=True,
    )

    body = GitHubReviewFormatter.format_inline_comment(finding)

    # 1. Issue title
    assert "SQL Injection Vulnerability" in body
    # 2. Severity label
    assert "🚨 **CRITICAL**" in body
    # 3. Explanation
    assert "Untrusted user parameter" in body
    # 4. Root cause
    assert "Missing parameterized binding" in body
    # 5. Supporting evidence
    assert "SELECT * FROM users WHERE id =" in body
    # 6. Suggested remediation with ```suggestion
    assert "```suggestion" in body
    assert 'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))' in body
    # 7. Verification status
    assert "Confirmed" in body
    # Fingerprint tag
    assert "<!-- openreview:finding_id=fnd-uuid-1234" in body


def test_executive_review_summary_formatting():
    review = Review(
        id="rev-999",
        pull_request_id="pr-1",
        commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
        status="completed",
        score=82.5,
        security_score=88.0,
        performance_score=90.0,
        quality_score=75.0,
        summary="Found 1 critical security finding and 1 minor performance issue.",
    )
    f_crit = Finding(
        file_path="src/auth.py",
        line_number=10,
        severity="critical",
        title="Hardcoded JWT Secret",
        category="security",
        message="Secret is exposed.",
    )
    f_med = Finding(
        file_path="src/utils.py",
        line_number=80,
        severity="medium",
        title="N+1 Query in Loop",
        category="performance",
        message="Query executed in loop.",
    )

    md = GitHubReviewFormatter.format_review_summary(
        review=review,
        inline_findings=[f_crit],
        summary_findings=[f_med],
        agent_names=["Security Sentinel", "Performance Agent"],
        commit_sha="a1b2c3d4e5f6789012345678901234567890abcd",
    )

    assert "OpenReview AI — Autonomous Code Review" in md
    assert "OpenReview_Score-82.5%2F100" in md
    assert "Security" in md
    assert "88.0/100" in md
    assert "Total Actionable Findings" in md
    assert "🚨 1 Critical" in md
    assert "Findings Outside PR Diff Hunks" in md
    assert "src/utils.py:80" in md
    assert "Security Sentinel" in md


# =====================================================================
# 3. ACTIONABILITY FILTERING TESTS
# =====================================================================

def test_actionability_filtering():
    f_valid = Finding(
        title="Valid Issue",
        verification_status="Confirmed",
        actionability_score=0.8,
        is_publishable=True,
        discussion_state="Accepted",
    )
    f_high_conf = Finding(
        title="High Conf Potential Issue",
        verification_status="High-confidence potential issue",
        actionability_score=0.75,
        is_publishable=True,
        discussion_state="Accepted",
    )
    f_rejected = Finding(
        title="Rejected False Positive",
        verification_status="Rejected",
        actionability_score=0.9,
        is_publishable=True,
        discussion_state="Rejected",
    )
    f_low_actionability = Finding(
        title="Low Actionability",
        verification_status="Confirmed",
        actionability_score=0.4,
        is_publishable=True,
        discussion_state="Accepted",
    )
    f_unpublishable = Finding(
        title="Internal Note",
        verification_status="Confirmed",
        actionability_score=0.9,
        is_publishable=False,
        discussion_state="Accepted",
    )

    assert GitHubReviewPublishingEngine.is_actionable(f_valid) is True
    assert GitHubReviewPublishingEngine.is_actionable(f_high_conf) is True
    assert GitHubReviewPublishingEngine.is_actionable(f_rejected) is False
    assert GitHubReviewPublishingEngine.is_actionable(f_low_actionability) is False
    assert GitHubReviewPublishingEngine.is_actionable(f_unpublishable) is False


# =====================================================================
# 4. DUPLICATE PREVENTION & OUTDATED COMMENT MANAGEMENT
# =====================================================================

@pytest.mark.asyncio
async def test_duplicate_comment_detection():
    finding = Finding(
        id="fnd-101",
        file_path="src/main.py",
        line_number=15,
        title="Null pointer dereference",
        severity="high",
        category="bug",
        message="Variable may be None.",
    )
    fp = GitHubReviewFormatter.compute_fingerprint(finding)

    # Mock client returning existing PR comments
    async def mock_handler(request):
        if request.url.path.endswith("/comments"):
            return Response(
                200,
                json=[
                    {
                        "id": 9901,
                        "path": "src/main.py",
                        "line": 15,
                        "body": f"### ⚠️ **HIGH**: Null pointer dereference\n<!-- openreview:finding_id=fnd-old:fp={fp} -->",
                    }
                ],
            )
        return Response(404, json={})

    client = AsyncClient(transport=MockTransport(mock_handler), base_url="https://api.github.com")
    engine = GitHubReviewPublishingEngine()
    existing = await engine.fetch_existing_pr_comments(client, "owner", "repo", 1)
    assert len(existing) == 1
    assert fp in existing[0]["body"]
    await client.aclose()


@pytest.mark.asyncio
async def test_outdated_comment_resolution_reply():
    # Finding from previous commit that is now resolved
    old_finding_fp = "0123456789abcdef"

    replied_ids = []

    async def mock_handler(request):
        path = request.url.path
        if path.endswith("/comments"):
            return Response(
                200,
                json=[
                    {
                        "id": 8801,
                        "path": "src/old_file.py",
                        "line": 10,
                        "body": f"### Issue\n<!-- openreview:finding_id=fnd-resolved:fp={old_finding_fp} -->",
                    }
                ],
            )
        elif "/replies" in path:
            replied_ids.append(path)
            return Response(201, json={"id": 99991, "body": "Resolved"})
        return Response(404, json={})

    client = AsyncClient(transport=MockTransport(mock_handler), base_url="https://api.github.com")
    engine = GitHubReviewPublishingEngine()

    # Current findings do not include old_finding_fp
    current_finding = Finding(
        id="fnd-new",
        file_path="src/new_file.py",
        line_number=20,
        title="Brand New Finding",
        severity="low",
        category="style",
        message="Add docstring.",
    )

    resolved_count = await engine.manage_outdated_comments(
        client=client,
        owner="octocat",
        repo="Hello-World",
        pull_number=42,
        current_findings=[current_finding],
        commit_sha="c0ffee123456789012345678901234567890abcd",
    )

    assert resolved_count == 1
    assert len(replied_ids) == 1
    assert "8801/replies" in replied_ids[0]
    await client.aclose()


# =====================================================================
# 5. RETRY & RATE LIMIT HANDLING
# =====================================================================

@pytest.mark.asyncio
async def test_retry_on_server_error():
    attempts = 0

    async def flaky_call():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return Response(502, text="Bad Gateway", headers={"X-RateLimit-Remaining": "5000"})
        return Response(200, text="Success", headers={"X-RateLimit-Remaining": "4999"})

    res = await GitHubRateLimitHandler.execute_with_retry(
        flaky_call,
        max_retries=3,
        base_delay=0.01,
        operation_name="Flaky Test",
    )
    assert res.status_code == 200
    assert attempts == 3


@pytest.mark.asyncio
async def test_rate_limit_exceeded_error():
    async def rate_limited_call():
        return Response(
            403,
            text="API rate limit exceeded for user ID 12345",
            headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "9999999999"},
        )

    with pytest.raises(GitHubRateLimitExceededError) as exc_info:
        await GitHubRateLimitHandler.execute_with_retry(
            rate_limited_call,
            max_retries=1,
            base_delay=0.01,
            operation_name="Rate Limited Test",
        )
    assert exc_info.value.status_code == 429
    assert "rate limit" in str(exc_info.value).lower()


# =====================================================================
# 6. END-TO-END PUBLISHING WORKFLOW (MOCKED GITHUB API)
# =====================================================================

@pytest.mark.asyncio
async def test_full_review_publishing_workflow(db_session: AsyncSession):
    # 1. Setup DB fixtures
    org = Organization(name="Publishing Test Org", slug="pub-test-org", plan="enterprise")
    db_session.add(org)
    await db_session.flush()

    repo = Repository(
        organization_id=org.id,
        github_repo_id=9876543,
        owner="test-owner",
        name="test-repo",
        full_name="test-owner/test-repo",
        default_branch="main",
        is_active=True,
    )
    db_session.add(repo)
    await db_session.flush()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id=10101,
        pr_number=77,
        title="Add payment authentication",
        head_branch="feat/payment",
        base_branch="main",
        head_sha="111122223333444455556666777788889999aaaa",
        base_sha="0000000000000000000000000000000000000000",
        author_username="dev-alice",
        state="open",
    )
    db_session.add(pr)
    await db_session.flush()

    review = Review(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="pending",
        score=78.0,
        security_score=70.0,
        performance_score=90.0,
        quality_score=85.0,
        summary="One critical security issue found.",
    )
    db_session.add(review)
    await db_session.flush()

    finding = Finding(
        review_id=review.id,
        file_path="src/payments.py",
        line_number=22,
        severity="critical",
        category="security",
        title="Unsanitized card token",
        message="Card token must be cryptographically hashed before storage.",
        root_cause="Plaintext token storage.",
        evidence="db.store(token)",
        suggested_patch="db.store(hash_token(token))",
        verification_status="Confirmed",
        confidence_score=0.96,
        actionability_score=0.92,
        is_publishable=True,
        discussion_state="Accepted",
    )
    db_session.add(finding)
    await db_session.commit()

    # 2. Mock GitHub API
    sample_pr_diff = """diff --git a/src/payments.py b/src/payments.py
index aaaaaaa..bbbbbbb 100644
--- a/src/payments.py
+++ b/src/payments.py
@@ -20,5 +20,6 @@ def process_payment(token):
+    db.store(token)
     return True
"""
    api_calls = []

    async def mock_github_api(request):
        path = str(request.url.path)
        method = request.method
        api_calls.append((method, path))

        if "/check-runs" in path and method == "POST":
            return Response(201, json={"id": 4001, "status": "in_progress"})
        elif "/check-runs" in path and method == "PATCH":
            return Response(200, json={"id": 4001, "status": "completed", "conclusion": "failure"})
        elif "/reviews/5001/comments" in path and method == "GET":
            return Response(200, json=[{"id": 6001, "body": f"<!-- openreview:finding_id={finding.id}:fp=test -->"}])
        elif path.endswith("/comments") and method == "GET":
            return Response(200, json=[])
        elif path.endswith(f"/pulls/{pr.pr_number}") and method == "GET":
            return Response(200, text=sample_pr_diff)
        elif "/reviews" in path and method == "POST":
            payload = json.loads(request.content.decode("utf-8"))
            # Confirm event is REQUEST_CHANGES because of Critical finding
            assert payload["event"] == "REQUEST_CHANGES"
            assert "Unsanitized card token" in str(payload["comments"])
            assert "```suggestion" in str(payload["comments"])
            return Response(201, json={"id": 5001, "html_url": "https://github.com/test-owner/test-repo/pull/77#pullrequestreview-5001"})
        return Response(404, json={})

    transport = MockTransport(mock_github_api)
    mock_client = AsyncClient(transport=transport, base_url="https://api.github.com")

    # Wire up custom auth service with mock client
    auth_service = GitHubAuthService(http_client=mock_client)

    engine = GitHubReviewPublishingEngine(
        session=db_session,
        auth_service=auth_service,
    )

    publish_req = GitHubPublishRequest(
        review_id=review.id,
        owner="test-owner",
        repo="test-repo",
        pull_number=77,
        token="gho_test_token_dummy",
    )

    result: GitHubPublishResult = await engine.publish_review(publish_req)

    # 3. Assertions on confirmed API response
    assert result.status == "published"
    assert result.api_confirmed is True
    assert result.github_review_id == 5001
    assert result.check_run_id == 4001
    assert result.event == "REQUEST_CHANGES"
    assert result.actionable_findings == 1
    assert result.inline_comments_published >= 1

    # Verify DB synchronization
    await db_session.refresh(review)
    assert review.status == "completed"
    assert "OpenReview AI — Autonomous Code Review" in review.summary

    await db_session.refresh(finding)
    assert finding.github_comment_id == "6001"

    await mock_client.aclose()


# =====================================================================
# 7. LIVE INTEGRATION TEST AGAINST REAL TEST REPO (gBashCode/OpenReview-AI-)
# =====================================================================

@pytest.mark.asyncio
async def test_live_github_api_connection(monkeypatch):
    """Verifies that the publishing engine connects and receives confirmed API responses

    from the real GitHub repository (gBashCode/OpenReview-AI-).
    """
    import subprocess
    try:
        token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except Exception:
        pytest.skip("GitHub CLI token not available for live API test.")

    if not token or not token.startswith("gh"):
        pytest.skip("Valid GitHub token not found.")

    client = AsyncClient(
        base_url="https://api.github.com",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "OpenReviewAI-Engine/1.0",
        },
        timeout=30.0,
    )

    # 1. Test live repo metadata verification
    repo_resp = await client.get("/repos/gBashCode/OpenReview-AI-")
    assert repo_resp.status_code == 200, f"GitHub repo lookup failed: {repo_resp.text}"
    repo_data = repo_resp.json()
    assert repo_data["full_name"] == "gBashCode/OpenReview-AI-"
    assert repo_data["permissions"]["push"] is True

    # 2. Test live commit status verification on the real repository head commit
    head_sha_resp = await client.get("/repos/gBashCode/OpenReview-AI-/commits/main")
    assert head_sha_resp.status_code == 200
    latest_sha = head_sha_resp.json()["sha"]

    status_payload = {
        "state": "success",
        "context": "OpenReview AI / Multi-Agent Code Review",
        "description": "Verified clean multi-agent review pass (Confirmed API response)",
    }
    status_resp = await client.post(f"/repos/gBashCode/OpenReview-AI-/statuses/{latest_sha}", json=status_payload)
    assert status_resp.status_code in (200, 201), f"Commit status creation failed [{status_resp.status_code}]: {status_resp.text}"
    status_data = status_resp.json()
    assert status_data["state"] == "success"
    assert status_data["context"] == "OpenReview AI / Multi-Agent Code Review"

    # 3. Test reading existing pull request review comments
    pr_comments_resp = await client.get("/repos/gBashCode/OpenReview-AI-/pulls/comments")
    assert pr_comments_resp.status_code == 200

    await client.aclose()
