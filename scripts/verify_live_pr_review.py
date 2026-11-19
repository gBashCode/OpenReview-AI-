#!/usr/bin/env python3
"""OpenReview AI - Live GitHub PR Review Execution & Publishing.

Connects to the local OpenReview AI backend, analyzes PR #5 on gBashCode/OpenReview-AI-,
runs multi-agent deliberation, and publishes the review scorecard and inline comments
directly to GitHub Pull Request #5 via the official GitHub API.
"""

import os
import sys
import time
import httpx

STAGING_API_URL = os.getenv("STAGING_API_URL", "http://127.0.0.1:8000").rstrip("/")
GITHUB_REPO_OWNER = "gBashCode"
GITHUB_REPO_NAME = "OpenReview-AI-"
PR_NUMBER = 5
PR_HEAD_SHA = "a8ee1ce5b54734f7a0e710f0628bf070545485e0"

# Auto-load token from .env if needed
GITHUB_TOKEN = os.getenv("TEST_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("GITHUB_TOKEN="):
                GITHUB_TOKEN = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                break

print("=" * 80)
print(f" OPENREVIEW AI - LIVE PULL REQUEST REVIEW VERIFICATION (PR #{PR_NUMBER})")
print("=" * 80)
print(f"Target API:           {STAGING_API_URL}")
print(f"Target Repository:    {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
print(f"Target Pull Request:  #{PR_NUMBER}")
print(f"GitHub Token Status:  {'Configured' if GITHUB_TOKEN else 'MISSING (required for live GitHub publishing)'}")
print("=" * 80)


def run_live_review():
    client = httpx.Client(base_url=STAGING_API_URL, timeout=60.0)

    # 1. Authenticate
    print("\n[1/5] Authenticating User...")
    user_email = f"live-reviewer-{int(time.time())}@openreview.ai"
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "username": f"live_rev_{int(time.time())}",
            "full_name": "Live Review Bot",
            "password": "LiveReviewPass123!",
        },
    )
    if reg_resp.status_code in (200, 201):
        token = reg_resp.json().get("token", {}).get("access_token")
    else:
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": user_email, "password": "LiveReviewPass123!"},
        )
        token = login_resp.json().get("token", {}).get("access_token")

    assert token, f"Authentication failed: {reg_resp.text}"
    auth_headers = {"Authorization": f"Bearer {token}"}
    print("  ✓ Authenticated with backend API")

    # 2. Register or fetch repository
    print(f"\n[2/5] Registering {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}...")
    repo_resp = client.post(
        "/api/v1/repositories",
        json={
            "github_repo_id": 1463647103,  # Official GitHub repository ID
            "owner": GITHUB_REPO_OWNER,
            "name": GITHUB_REPO_NAME,
            "default_branch": "main",
            "description": "OpenReview AI Core Repository",
        },
        headers=auth_headers,
    )
    if repo_resp.status_code in (200, 201):
        repo_data = repo_resp.json()
    else:
        # Fetch existing
        list_resp = client.get("/api/v1/repositories", headers=auth_headers)
        repos = list_resp.json()
        repo_data = next((r for r in repos if r["name"] == GITHUB_REPO_NAME), None)
        if not repo_data:
            # Fallback create with pseudo ID if 1463647103 conflicted
            repo_resp = client.post(
                "/api/v1/repositories",
                json={
                    "github_repo_id": int(time.time()),
                    "owner": GITHUB_REPO_OWNER,
                    "name": GITHUB_REPO_NAME,
                    "default_branch": "main",
                    "description": "OpenReview AI Core Repository",
                },
                headers=auth_headers,
            )
            repo_data = repo_resp.json()

    repo_id = repo_data["id"]
    print(f"  ✓ Repository Active: {repo_data['full_name']} (ID: {repo_id})")

    # 3. Create or Fetch PR #5
    print(f"\n[3/5] Setting up Pull Request #{PR_NUMBER}...")
    sample_diff = (
        "diff --git a/backend/app/demo_sample.py b/backend/app/demo_sample.py\n"
        "new file mode 100644\n"
        "index 0000000..115f04d\n"
        "--- /dev/null\n"
        "+++ b/backend/app/demo_sample.py\n"
        "@@ -0,0 +1,9 @@\n"
        '+\"\"\"Sample utility demonstrating OpenReview AI automated review engine.\"\"\"\n'
        "+\n"
        "+from typing import List, Optional\n"
        "+\n"
        "+\n"
        "+def calculate_average(values: Optional[List[int]]) -> float:\n"
        '+\"\"\"Calculate the arithmetic mean of a list of numbers.\"\"\"\n'
        "+    # Intentional unhandled edge-case: empty or None list\n"
        "+    return sum(values) / len(values)\n"
    )

    pr_resp = client.post(
        "/api/v1/pull-requests",
        json={
            "repository_id": repo_id,
            "pr_number": PR_NUMBER,
            "title": "feat: add calculate_average sample utility",
            "head_branch": "test/openreview-demo",
            "base_branch": "main",
            "head_sha": PR_HEAD_SHA,
            "base_sha": "d8b7b97ff259b1e18cfb0fec59d83c7c2038f962",
            "author_username": "akashhg2007",
            "diff_summary": "1 file changed, 9 insertions",
        },
        headers=auth_headers,
    )
    if pr_resp.status_code in (200, 201):
        pr_data = pr_resp.json()
    else:
        # Fetch PR
        prs_resp = client.get(f"/api/v1/pull-requests?repository_id={repo_id}", headers=auth_headers)
        prs = prs_resp.json()
        pr_data = next((p for p in prs if p["pr_number"] == PR_NUMBER), None)
        assert pr_data, f"Failed to retrieve or create PR #{PR_NUMBER}: {pr_resp.text}"

    pr_id = pr_data["id"]
    print(f"  ✓ Pull Request Linked: #{PR_NUMBER} (ID: {pr_id})")

    # 4. Trigger Code Review & Deliberation
    print("\n[4/5] Executing Multi-Agent Code Review & Deliberation on PR...")
    review_resp = client.post(
        "/api/v1/reviews",
        json={
            "pull_request_id": pr_id,
            "target_commit": PR_HEAD_SHA,
            "is_incremental": False,
        },
        headers=auth_headers,
    )
    assert review_resp.status_code in (200, 201), f"Review trigger failed: {review_resp.text}"
    review_data = review_resp.json()
    review_id = review_data["id"]

    # Execute deliberation
    delib_resp = client.post(
        f"/api/v1/reviews/{review_id}/conference/deliberate",
        json={"max_rounds": 2, "custom_diff": sample_diff},
        headers=auth_headers,
    )
    assert delib_resp.status_code == 200, f"Deliberation failed: {delib_resp.text}"
    delib_data = delib_resp.json()
    print(f"  ✓ Multi-Agent Deliberation complete (Rounds: {delib_data.get('total_rounds', 2)})")

    # Fetch findings
    findings_resp = client.get(f"/api/v1/reviews/{review_id}/findings", headers=auth_headers)
    findings = findings_resp.json()
    print(f"  ✓ Detected & Verified Findings: {len(findings)} issues")
    for idx, f in enumerate(findings, 1):
        print(f"    [{idx}] [{f.get('severity', 'MEDIUM').upper()}] {f.get('title')} ({f.get('file_path')}:{f.get('line_start')})")

    # 5. Publish to GitHub
    print(f"\n[5/5] Publishing Review directly to GitHub Pull Request #{PR_NUMBER}...")
    publish_resp = client.post(
        f"/api/v1/reviews/{review_id}/publish",
        json={"review_id": review_id, "token": GITHUB_TOKEN},
        headers=auth_headers,
    )
    assert publish_resp.status_code in (200, 201), f"GitHub Publishing failed: {publish_resp.text}"
    pub_result = publish_resp.json()
    print(f"  ✓ GitHub Publishing Result: Status={pub_result.get('status')}")
    print(f"  ✓ Published Comments:       {pub_result.get('published_comments_count')}")
    print(f"  ✓ Check Run ID:             {pub_result.get('check_run_id')}")
    if pub_result.get("github_review_url"):
        print(f"  ✓ GitHub Review Link:       {pub_result.get('github_review_url')}")
    print(f"  ✓ Direct PR URL:            https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/pull/{PR_NUMBER}")

    print("\n" + "=" * 80)
    print(" LIVE GITHUB PULL REQUEST REVIEW COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_live_review()
