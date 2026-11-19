"""Comprehensive tests for GitHub App integration, webhook signatures, diffs, and review publishing."""

import hashlib
import hmac
import json
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient, Response
from app.core.config import get_settings
from app.github.github_auth_service import GitHubAuthService
from app.github.github_diff_service import GitHubDiffService
from app.github.github_pull_request_service import GitHubPullRequestService
from app.github.github_repository_service import GitHubRepositoryService
from app.github.github_review_service import GitHubReviewService
from app.github.github_webhook_service import GitHubWebhookService
from app.github.schemas import (
    GitHubCheckRunAnnotation,
    GitHubCheckRunCreate,
    GitHubCheckRunOutput,
    GitHubInlineComment,
)


@pytest.fixture(scope="session")
def rsa_test_key():
    """Generates an ephemeral RSA private key for testing RS256 signing."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    return pem


@pytest.mark.asyncio
async def test_github_auth_jwt_and_token_exchange(rsa_test_key: str, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "GITHUB_APP_ID", "123456")
    monkeypatch.setattr(settings, "GITHUB_APP_PRIVATE_KEY", rsa_test_key)

    # Mock HTTP client for token exchange
    async def mock_handler(request):
        assert "Authorization" in request.headers
        assert request.headers["Authorization"].startswith("Bearer eyJ")
        return Response(
            201,
            json={
                "token": "ghs_test_access_token_12345",
                "expires_at": "2030-01-01T00:00:00Z",
                "permissions": {"pull_requests": "write", "checks": "write"},
            },
        )

    mock_client = AsyncClient(transport=ASGITransport(app=None))  # transport mock
    # Use httpx.MockTransport
    from httpx import MockTransport
    transport = MockTransport(mock_handler)
    client = AsyncClient(transport=transport)

    auth_service = GitHubAuthService(http_client=client)
    GitHubAuthService.clear_cache()

    # 1. Test JWT generation
    jwt_token = auth_service.generate_app_jwt()
    assert jwt_token.startswith("eyJ")

    # 2. Test token exchange
    token = await auth_service.get_installation_access_token(installation_id=98765)
    assert token == "ghs_test_access_token_12345"

    # 3. Test token caching (should not invoke network second time)
    cached_token = await auth_service.get_installation_access_token(installation_id=98765)
    assert cached_token == token

    await client.aclose()


@pytest.mark.asyncio
async def test_webhook_hmac_signature_verification(monkeypatch):
    settings = get_settings()
    test_secret = "test_webhook_super_secret"
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", test_secret)

    payload_body = json.dumps({"action": "opened", "number": 1}).encode("utf-8")

    # Compute valid signature
    valid_sig = "sha256=" + hmac.new(test_secret.encode("utf-8"), payload_body, hashlib.sha256).hexdigest()
    assert GitHubWebhookService.verify_signature(payload_body, valid_sig) is True

    # Invalid signature
    assert GitHubWebhookService.verify_signature(payload_body, "sha256=invalidhex") is False

    # Missing signature
    assert GitHubWebhookService.verify_signature(payload_body, None) is False


@pytest.mark.asyncio
async def test_webhook_endpoint_ping(async_client: AsyncClient, monkeypatch):
    settings = get_settings()
    secret = "secret123"
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", secret)

    ping_payload = {"zen": "Keep it logically awesome."}
    raw = json.dumps(ping_payload).encode("utf-8")
    sig = "sha256=" + hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()

    headers = {
        "X-GitHub-Event": "ping",
        "X-Hub-Signature-256": sig,
        "X-GitHub-Delivery": "test-delivery-ping-1",
        "Content-Type": "application/json",
    }
    response = await async_client.post("/api/v1/github/webhook", content=raw, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "pong", "zen": "Keep it logically awesome."}

    # Test idempotency deduplication on same delivery
    dup_res = await async_client.post("/api/v1/github/webhook", content=raw, headers=headers)
    assert dup_res.status_code == 200
    assert dup_res.json()["status"] == "duplicate_ignored"


@pytest.mark.asyncio
async def test_webhook_pull_request_opened_and_synchronize(async_client: AsyncClient, monkeypatch):
    settings = get_settings()
    secret = "pr_secret"
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", secret)

    # 1. PR Opened Event
    opened_payload = {
        "action": "opened",
        "number": 101,
        "pull_request": {
            "id": 554433,
            "number": 101,
            "title": "feat: add payment gateway checkout",
            "body": "Implements Stripe SDK integration",
            "state": "open",
            "head": {"sha": "1111111111111111111111111111111111111111", "ref": "feat/payments"},
            "base": {"sha": "0000000000000000000000000000000000000000", "ref": "main"},
            "user": {"login": "stripe-eng"},
            "merged": False,
        },
        "repository": {
            "id": 998811,
            "name": "ecommerce-api",
            "full_name": "acme/ecommerce-api",
            "owner": {"login": "acme"},
            "default_branch": "main",
            "clone_url": "https://github.com/acme/ecommerce-api.git",
        },
        "installation": {"id": 12345},
    }
    raw_opened = json.dumps(opened_payload).encode("utf-8")
    sig_opened = "sha256=" + hmac.new(secret.encode("utf-8"), raw_opened, hashlib.sha256).hexdigest()

    res_opened = await async_client.post(
        "/api/v1/github/webhook",
        content=raw_opened,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": sig_opened,
            "X-GitHub-Delivery": "delivery-pr-open-101",
            "Content-Type": "application/json",
        },
    )
    assert res_opened.status_code == 200
    data_opened = res_opened.json()
    assert data_opened["status"] == "review_triggered"
    assert data_opened["action"] == "opened"
    assert data_opened["review_id"] is not None

    # 2. PR Synchronize Event (developer pushed new commit to branch)
    sync_payload = dict(opened_payload)
    sync_payload["action"] = "synchronize"
    sync_payload["pull_request"]["head"]["sha"] = "2222222222222222222222222222222222222222"

    raw_sync = json.dumps(sync_payload).encode("utf-8")
    sig_sync = "sha256=" + hmac.new(secret.encode("utf-8"), raw_sync, hashlib.sha256).hexdigest()

    res_sync = await async_client.post(
        "/api/v1/github/webhook",
        content=raw_sync,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": sig_sync,
            "X-GitHub-Delivery": "delivery-pr-sync-101",
            "Content-Type": "application/json",
        },
    )
    assert res_sync.status_code == 200
    data_sync = res_sync.json()
    assert data_sync["status"] == "review_triggered"
    assert data_sync["action"] == "synchronize"
    assert data_sync["head_sha"] == "2222222222222222222222222222222222222222"

    # 3. PR Closed Event
    closed_payload = dict(opened_payload)
    closed_payload["action"] = "closed"
    closed_payload["pull_request"]["merged"] = True
    raw_closed = json.dumps(closed_payload).encode("utf-8")
    sig_closed = "sha256=" + hmac.new(secret.encode("utf-8"), raw_closed, hashlib.sha256).hexdigest()

    res_closed = await async_client.post(
        "/api/v1/github/webhook",
        content=raw_closed,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": sig_closed,
            "X-GitHub-Delivery": "delivery-pr-close-101",
            "Content-Type": "application/json",
        },
    )
    assert res_closed.status_code == 200
    data_closed = res_closed.json()
    assert data_closed["status"] == "closed"
    assert data_closed["merged"] is True


@pytest.mark.asyncio
async def test_webhook_installation_lifecycle(async_client: AsyncClient, monkeypatch):
    settings = get_settings()
    secret = "inst_secret"
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", secret)

    # 1. Installation Created
    inst_created_payload = {
        "action": "created",
        "installation": {
            "id": 778899,
            "account": {"login": "OpenSourceOrg", "type": "Organization"},
            "permissions": {"pull_requests": "write", "contents": "read"},
        },
    }
    raw_inst = json.dumps(inst_created_payload).encode("utf-8")
    sig_inst = "sha256=" + hmac.new(secret.encode("utf-8"), raw_inst, hashlib.sha256).hexdigest()

    res = await async_client.post(
        "/api/v1/github/webhook",
        content=raw_inst,
        headers={
            "X-GitHub-Event": "installation",
            "X-Hub-Signature-256": sig_inst,
            "X-GitHub-Delivery": "delivery-inst-created-1",
            "Content-Type": "application/json",
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "created"

    # 2. Installation Deleted
    inst_deleted_payload = dict(inst_created_payload)
    inst_deleted_payload["action"] = "deleted"
    raw_del = json.dumps(inst_deleted_payload).encode("utf-8")
    sig_del = "sha256=" + hmac.new(secret.encode("utf-8"), raw_del, hashlib.sha256).hexdigest()

    del_res = await async_client.post(
        "/api/v1/github/webhook",
        content=raw_del,
        headers={
            "X-GitHub-Event": "installation",
            "X-Hub-Signature-256": sig_del,
            "X-GitHub-Delivery": "delivery-inst-del-1",
            "Content-Type": "application/json",
        },
    )
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"


@pytest.mark.asyncio
async def test_github_diff_parsing():
    sample_patch = """@@ -10,4 +10,6 @@ def process_transaction():
     validate_card()
+    # Tokenize customer card
+    token = tokenize()
     charge_card()
-    log_card_number()
+    log_redacted()
"""
    lines = GitHubDiffService.parse_patch_lines(sample_patch)
    assert len(lines) > 0
    # Line 11 is added tokenization
    added_lines = [l for l in lines if "# Tokenize" in l[2]]
    assert len(added_lines) == 1
    assert added_lines[0][1] == 11  # file_line_number


@pytest.mark.asyncio
async def test_github_review_formatting_and_mock_publishing(rsa_test_key: str, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "GITHUB_APP_ID", "123456")
    monkeypatch.setattr(settings, "GITHUB_APP_PRIVATE_KEY", rsa_test_key)

    # Test markdown formatter
    summary_md = GitHubReviewService.format_review_summary_markdown(
        score=95.0,
        security_score=98.0,
        performance_score=92.0,
        quality_score=95.0,
        summary_text="No blocking vulnerabilities found. Excellent code health.",
        findings_count=1,
        agent_names=["Security Sentinel", "Bug Hunter"],
    )
    assert "OpenReview AI — Autonomous Code Review" in summary_md
    assert "Quality Dimension" in summary_md
    assert "Security Sentinel" in summary_md

    # Test Mock publishing inline comment and review
    from httpx import MockTransport

    async def mock_github_api(request):
        path = str(request.url)
        if "/comments" in path:
            return Response(201, json={"id": 99881, "body": "Suggested fix"})
        elif "/reviews" in path:
            return Response(201, json={"id": 77661, "state": "COMMENTED"})
        elif "/check-runs" in path:
            return Response(201, json={"id": 55441, "status": "completed"})
        elif "/access_tokens" in path:
            return Response(201, json={"token": "ghs_mock", "expires_at": "2030-01-01T00:00:00Z"})
        return Response(404, json={})

    transport = MockTransport(mock_github_api)
    client = AsyncClient(transport=transport)
    auth_service = GitHubAuthService(http_client=client)
    review_service = GitHubReviewService(auth_service=auth_service)

    # 1. Publish inline comment
    comment_res = await review_service.publish_inline_comment(
        installation_id=1,
        owner="octocat",
        repo="Hello-World",
        pull_number=42,
        commit_sha="a" * 40,
        file_path="src/main.py",
        line=25,
        body="Use parameter binding instead of string concatenation to avoid SQL injection.",
    )
    assert comment_res["id"] == 99881

    # 2. Publish pull request review
    review_res = await review_service.publish_pull_request_review(
        installation_id=1,
        owner="octocat",
        repo="Hello-World",
        pull_number=42,
        commit_sha="a" * 40,
        summary_body=summary_md,
        inline_comments=[
            GitHubInlineComment(path="src/main.py", line=25, body="Security warning")
        ],
    )
    assert review_res["id"] == 77661

    # 3. Create Check Run
    check_run_res = await review_service.create_check_run(
        installation_id=1,
        owner="octocat",
        repo="Hello-World",
        check_run_in=GitHubCheckRunCreate(
            head_sha="a" * 40,
            status="completed",
            conclusion="success",
            output=GitHubCheckRunOutput(
                title="Code Quality Review: Passed",
                summary="Quality score: 95/100",
                annotations=[
                    GitHubCheckRunAnnotation(
                        path="src/main.py",
                        start_line=25,
                        end_line=25,
                        annotation_level="notice",
                        message="Verified clean parameters",
                    )
                ],
            ),
        ),
    )
    assert check_run_res["id"] == 55441

    await client.aclose()
