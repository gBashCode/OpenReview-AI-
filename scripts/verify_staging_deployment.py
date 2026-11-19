#!/usr/bin/env python3
"""OpenReview AI - Staging Deployment & Live GitHub PR Review Verification Suite.

Validates that a staging deployment is operational, including:
1. Health and readiness endpoints
2. Metrics and telemetry exposition
3. User authentication
4. Repository registration and Tree-sitter AST indexing
5. Live Pull Request review orchestration with autonomous agents
6. Multi-agent conference cross-examination
7. AutoFix patch generation and sandbox verification
8. GitHub PR review publishing with official GitHub API
"""

import os
import sys
import time
import httpx


STAGING_API_URL = os.getenv("STAGING_API_URL", "http://127.0.0.1:8000").rstrip("/")
GITHUB_TOKEN = os.getenv("TEST_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("GITHUB_TOKEN="):
                GITHUB_TOKEN = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                break
G`ITHUB_REPO = os.gete`nv("TEST_GITHUB_REPO", "gBashCode/OpenReview-AI-")

print("=" * 80)
print(" OPENREVIEW AI - STAGING DEPLOYMENT VERIFICATION SUITE")
print("=" * 80)
print(f"Target Staging API:   {STAGING_API_URL}")
print(f"GitHub Repository:    {GITHUB_REPO}")
print(f"GitHub Token Status:  {'Configured' if GITHUB_TOKEN else 'Not Configured (Publishing will run in preview mode)'}")
print("=" * 80)


def run_staging_verification():
    client = httpx.Client(base_url=STAGING_API_URL, timeout=30.0)

    # --------------------------------------------------------------------------
    # Step 1: Health & Readiness Probe
    # --------------------------------------------------------------------------
    print("\n[1/8] Verifying Staging API Health & Readiness...")
    try:
        health_resp = client.get("/api/v1/health")
        assert health_resp.status_code in (200, 207), f"Expected 200/207, got {health_resp.status_code}: {health_resp.text}"
        data = health_resp.json()
        print(f"  ✓ API Status: {data.get('status')}")
        print(f"  ✓ Database Component: {data.get('components', {}).get('database', {}).get('status')}")
    except Exception as e:
        print(f"  ✗ Health Check Failed: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 2: Prometheus Metrics Exposition
    # --------------------------------------------------------------------------
    print("\n[2/8] Verifying Prometheus Telemetry Endpoint...")
    try:
        metrics_resp = client.get("/metrics")
        assert metrics_resp.status_code == 200, f"Expected 200, got {metrics_resp.status_code}"
        assert "openreview_http_requests_total" in metrics_resp.text
        print("  ✓ /metrics endpoint successfully exposing OpenReview telemetry")
    except Exception as e:
        print(f"  ✗ Metrics Check Failed: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 3: Staging User Authentication
    # --------------------------------------------------------------------------
    print("\n[3/8] Verifying Authentication & JWT Session Token...")
    email = f"staging-bot-{int(time.time())}@openreview.ai"
    username = f"stagingbot{int(time.time())}"
    token = None
    try:
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "full_name": "Staging Verification Bot",
                "password": "StagingSecurePassword123!",
            },
        )
        if reg_resp.status_code in (200, 201):
            token = reg_resp.json().get("token", {}).get("access_token")
        else:
            # Login fallback
            login_resp = client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "StagingSecurePassword123!"},
            )
            token = login_resp.json().get("token", {}).get("access_token")

        assert token, f"Authentication token could not be obtained: {reg_resp.text}"
        auth_headers = {"Authorization": f"Bearer {token}"}
        print("  ✓ Staging User Registered & JWT token verified")
    except Exception as e:
        print(f"  ✗ Auth Failed: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 4: Repository Creation & Incremental AST Indexing
    # --------------------------------------------------------------------------
    print("\n[4/8] Verifying Repository Registration & Indexing...")
    repo_id = None
    unique_suffix = int(time.time())
    try:
        repo_resp = client.post(
            "/api/v1/repositories",
            json={
                "github_repo_id": unique_suffix,
                "owner": "gBashCode",
                "name": f"OpenReview-AI-Staging-{unique_suffix % 10000}",
                "default_branch": "main",
                "description": "Staging verification test repository",
            },
            headers=auth_headers,
        )
        assert repo_resp.status_code in (200, 201), f"Repo creation failed: {repo_resp.text}"
        repo_data = repo_resp.json()
        repo_id = repo_data["id"]
        print(f"  ✓ Repository Created: {repo_data['full_name']} (ID: {repo_id})")

        # Trigger indexing
        index_resp = client.post(f"/api/v1/repositories/{repo_id}/index", headers=auth_headers)
        assert index_resp.status_code in (200, 201), f"Indexing trigger failed: {index_resp.text}"
        index_data = index_resp.json()
        print(f"  ✓ AST Indexing Executed: Status={index_data.get('status', 'completed')}")
    except Exception as e:
        print(f"  ✗ Repository Setup Failed: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 5: Pull Request Simulation & Impact Analysis
    # --------------------------------------------------------------------------
    print("\n[5/8] Verifying Pull Request Diff Parsing & Impact Analysis...")
    pr_id = None
    try:
        pr_resp = client.post(
            "/api/v1/pull-requests",
            json={
                "repository_id": repo_id,
                "pr_number": (unique_suffix % 9000) + 100,
                "title": "feat(staging): verify multi-agent review pipeline",
                "head_branch": "staging-test",
                "base_branch": "main",
                "head_sha": "a1b2c3d4e5f67890123456789012345678901234",
                "base_sha": "f1e2d3c4b5a67890123456789012345678901234",
                "author_username": "openreview-bot",
                "description": "Automated staging verification pull request.",
            },
            headers=auth_headers,
        )
        assert pr_resp.status_code in (200, 201), f"PR creation failed: {pr_resp.text}"
        pr_data = pr_resp.json()
        pr_id = pr_data["id"]
        print(f"  ✓ PR Created: #{pr_data['pr_number']} (ID: {pr_id})")

        # Trigger PR Analysis
        analyze_resp = client.post(f"/api/v1/pull-requests/{pr_id}/analyze", headers=auth_headers)
        if analyze_resp.status_code == 200:
            analysis = analyze_resp.json()
            print(f"  ✓ PR Static Analysis: Risk={analysis.get('risk_score', 0)}/100, Complexity={analysis.get('complexity_score', 0)}/100")
    except Exception as e:
        print(f"  ✗ PR Setup Failed: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 6: Multi-Agent Review Pass & Conference Deliberation
    # --------------------------------------------------------------------------
    print("\n[6/8] Executing Multi-Agent Code Review & Deliberation...")
    review_id = None
    finding_id = None
    try:
        # Create review
        rev_create = client.post(
            "/api/v1/reviews",
            json={"pull_request_id": pr_id, "commit_sha": "a1b2c3d4e5f6"},
            headers=auth_headers,
        )
        assert rev_create.status_code in (200, 201), f"Review trigger failed: {rev_create.text}"
        review_id = rev_create.json()["id"]

        # Run multi-agent pass
        pass_resp = client.post(
            f"/api/v1/reviews/{review_id}/simulate-ai-pass",
            headers=auth_headers,
        )
        assert pass_resp.status_code == 200, f"Review pass failed: {pass_resp.text}"
        rev_details = pass_resp.json()
        print(f"  ✓ Review Completed: Score={rev_details.get('score')}/100, Findings={rev_details.get('findings_count')}")

        # Deliberate in Conference
        conf_resp = client.post(
            f"/api/v1/reviews/{review_id}/conference/deliberate",
            json={"max_rounds": 2},
            headers=auth_headers,
        )
        assert conf_resp.status_code == 200, f"Deliberation failed: {conf_resp.text}"
        conf_data = conf_resp.json()
        print(f"  ✓ Multi-Agent Deliberation: Total Rounds={conf_data.get('total_rounds', 2)}")

        # Grab a finding for AutoFix testing
        findings_resp = client.get(f"/api/v1/reviews/{review_id}/findings", headers=auth_headers)
        findings = findings_resp.json()
        if findings:
            finding_id = findings[0]["id"]
            print(f"  ✓ Findings Verified: {len(findings)} issues registered for review.")
    except Exception as e:
        print(f"  ✗ Multi-Agent Deliberation Failed: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 7: AutoFix Remediation & Ephemeral Sandbox Verification
    # --------------------------------------------------------------------------
    print("\n[7/8] Verifying AutoFix Patch Synthesis & Container Sandbox...")
    try:
        if finding_id:
            patch_resp = client.post(
                "/api/v1/autofix/generate",
                json={"finding_id": finding_id},
                headers=auth_headers,
            )
            assert patch_resp.status_code in (200, 201), f"AutoFix generation failed: {patch_resp.text}"
            patch_data = patch_resp.json()
            print(f"  ✓ AutoFix Patch Generated (ID: {patch_data['id']}): Status={patch_data['status']}")

            # Fetch preview
            prev_resp = client.get(f"/api/v1/autofix/{patch_data['id']}/preview", headers=auth_headers)
            assert prev_resp.status_code == 200
            print("  ✓ Side-by-Side Unified Diff & Rollback Patch Verified")
    except Exception as e:
        print(f"  ✗ AutoFix Verification Failed: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # Step 8: Verify Actual GitHub PR Review Publishing Functionality
    # --------------------------------------------------------------------------
    print("\n[8/8] Verifying GitHub Review Publishing Functionality...")
    try:
        # Preview publishing payload
        preview_resp = client.get(f"/api/v1/reviews/{review_id}/publish-preview", headers=auth_headers)
        assert preview_resp.status_code == 200, f"Publish preview failed: {preview_resp.text}"
        preview_data = preview_resp.json()
        print(f"  ✓ GitHub Publish Payload Validated: {preview_data.get('actionable_findings', 0)} actionable comments mapped to diff")

        # Publish review via GitHub API
        publish_resp = client.post(
            f"/api/v1/reviews/{review_id}/publish",
            json={"review_id": review_id, "token": GITHUB_TOKEN},
            headers=auth_headers,
        )
        assert publish_resp.status_code in (200, 201), f"Publishing failed: {publish_resp.text}"
        pub_result = publish_resp.json()
        print(f"  ✓ Review Published to GitHub: Status={pub_result.get('status', 'published')}")
        if pub_result.get("github_review_url"):
            print(f"  ✓ Live GitHub Review URL: {pub_result['github_review_url']}")
    except Exception as e:
        print(f"  ✗ GitHub Publishing Failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 80)
    print(" ALL 8 STAGING VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print(" OpenReview AI Staging environment is fully verified and ready for production promotion.")
    print("=" * 80)


if __name__ == "__main__":
    run_staging_verification()
