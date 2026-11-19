#!/usr/bin/env python3
"""Seed comprehensive real data for OpenReview AI local demonstration.

Ensures the database has:
- Authenticated demo user: architect@openreview.ai (Password: OpenReview2026!)
- Connected repositories (gBashCode/OpenReview-AI- & payment-service)
- Active Pull Requests with unified diffs
- Code reviews with multi-agent council findings across Bug, Security, and Performance
- Deliberation conference discussions and verification arbiter decisions
- AutoFix patches with side-by-side unified diffs ready for review
"""

import sys
import os
import time
import httpx

API_BASE = "http://127.0.0.1:8000/api/v1"

def seed():
    print("=" * 70)
    print(" SEEDING OPENREVIEW AI DATABASE FOR FULL WEB UI INTERACTION")
    print("=" * 70)

    client = httpx.Client(timeout=30.0)

    # 1. Login or Register demo user
    print("\n[1/5] Ensuring 'architect@openreview.ai' is initialized...")
    user_token = None
    try:
        login_res = client.post(f"{API_BASE}/auth/login", json={
            "email": "architect@openreview.ai",
            "password": "OpenReview2026!"
        })
        if login_res.status_code == 200:
            user_token = login_res.json()["token"]["access_token"]
            print("  ✓ Logged in as architect@openreview.ai")
    except Exception as e:
        print(f"  Note: {e}")

    if not user_token:
        reg_res = client.post(f"{API_BASE}/auth/register", json={
            "email": "architect@openreview.ai",
            "username": "architect",
            "password": "OpenReview2026!",
            "full_name": "Lead Architect",
            "organization_name": "OpenReview Core"
        })
        assert reg_res.status_code in (200, 201), f"Registration failed: {reg_res.text}"
        user_token = reg_res.json()["token"]["access_token"]
        print("  ✓ Registered architect@openreview.ai")

    headers = {"Authorization": f"Bearer {user_token}"}

    # 2. Ensure Repositories
    print("\n[2/5] Creating demo repositories...")
    repos_to_create = [
        {
            "github_repo_id": 1463647103,
            "owner": "gBashCode",
            "name": "OpenReview-AI-",
            "default_branch": "main",
            "description": "Autonomous multi-agent code intelligence engine",
        },
        {
            "github_repo_id": 883921102,
            "owner": "gBashCode",
            "name": "payment-gateway-service",
            "default_branch": "main",
            "description": "High-throughput asynchronous payment processing service",
        }
    ]

    active_repos = []
    for r in repos_to_create:
        res = client.post(f"{API_BASE}/repositories", json=r, headers=headers)
        if res.status_code in (200, 201):
            repo = res.json()
            active_repos.append(repo)
            print(f"  ✓ Created repository: {repo['full_name']}")
        else:
            # Fetch existing
            list_res = client.get(f"{API_BASE}/repositories", headers=headers)
            for existing in list_res.json():
                if existing["name"] == r["name"]:
                    active_repos.append(existing)
                    print(f"  ✓ Found existing repository: {existing['full_name']}")
                    break

    main_repo = active_repos[0]

    # Index repository
    print("\n[3/5] Triggering AST symbol indexing...")
    idx_res = client.post(f"{API_BASE}/repositories/{main_repo['id']}/index", headers=headers)
    print(f"  ✓ Indexing status: {idx_res.status_code}")

    # 3. Create Pull Requests
    print("\n[4/5] Creating realistic Pull Requests...")
    diff_sample = (
        "diff --git a/backend/app/demo_sample.py b/backend/app/demo_sample.py\n"
        "new file mode 100644\n"
        "index 0000000..115f04d\n"
        "--- /dev/null\n"
        "+++ b/backend/app/demo_sample.py\n"
        "@@ -0,0 +1,15 @@\n"
        '+\"\"\"Sample utility demonstrating OpenReview AI automated review engine.\"\"\"\n'
        "+\n"
        "+from typing import List, Optional\n"
        "+\n"
        "+\n"
        "+def calculate_average(values: Optional[List[int]]) -> float:\n"
        '+\"\"\"Calculate the arithmetic mean of a list of numbers.\"\"\"\n'
        "+    # Bug: Unhandled NoneType and empty list ZeroDivisionError\n"
        "+    return sum(values) / len(values)\n"
        "+\n"
        "+def execute_query(conn, table_name: str):\n"
        "+    # Security vulnerability: SQL injection risk\n"
        "+    return conn.execute(f'SELECT * FROM {table_name}')\n"
    )

    pr_res = client.post(f"{API_BASE}/pull-requests", json={
        "repository_id": main_repo["id"],
        "pr_number": 5,
        "title": "feat: add calculate_average and database query utilities",
        "head_branch": "test/openreview-demo",
        "base_branch": "main",
        "head_sha": "a8ee1ce5b54734f7a0e710f0628bf070545485e0",
        "base_sha": "d8b7b97ff259b1e18cfb0fec59d83c7c2038f962",
        "author_username": "akashhg2007",
        "diff_summary": "1 file changed, 15 insertions",
    }, headers=headers)
    if pr_res.status_code in (200, 201):
        pr = pr_res.json()
    else:
        # Get existing PR
        list_prs = client.get(f"{API_BASE}/pull-requests?repository_id={main_repo['id']}", headers=headers).json()
        pr = next((p for p in list_prs if p["pr_number"] == 5), list_prs[0] if list_prs else None)

    print(f"  ✓ Active Pull Request: #{pr['pr_number']} - {pr['title']} (ID: {pr['id']})")

    # Analyze PR impact
    an_res = client.post(f"{API_BASE}/pull-requests/{pr['id']}/analyze", headers=headers)
    print(f"  ✓ PR Risk Analysis: {an_res.json().get('risk_score', 15.0)}/100")

    # 4. Create Review and Findings
    print("\n[5/5] Creating and executing Code Review with findings...")
    rev_res = client.post(f"{API_BASE}/reviews", json={
        "pull_request_id": pr["id"],
        "target_commit": "a8ee1ce5b54734f7a0e710f0628bf070545485e0",
        "is_incremental": False
    }, headers=headers)
    assert rev_res.status_code in (200, 201), f"Review creation failed: {rev_res.text}"
    review = rev_res.json()
    review_id = review["id"]
    print(f"  ✓ Code Review created: {review_id}")

    # Deliberate
    delib_res = client.post(
        f"{API_BASE}/reviews/{review_id}/conference/deliberate",
        json={"max_rounds": 2, "custom_diff": diff_sample},
        headers=headers
    )
    print(f"  ✓ Deliberation completed: {delib_res.status_code}")

    # Create findings directly if agents had no API keys
    findings_list = client.get(f"{API_BASE}/reviews/{review_id}/findings", headers=headers).json()
    if not findings_list:
        print("  Generating verified demonstration findings for UI...")
        sample_findings = [
            {
                "review_id": review_id,
                "title": "Unhandled Empty List / NoneType causes ZeroDivisionError",
                "description": "Calling `calculate_average` with an empty list or None raises ZeroDivisionError or TypeError on `sum(values) / len(values)`.",
                "file_path": "backend/app/demo_sample.py",
                "line_start": 9,
                "line_end": 10,
                "category": "bug",
                "severity": "high",
                "confidence": 0.95,
                "impact": "Uncaught exception causing 500 internal server error during analytics processing.",
                "root_cause": "Missing guard clause validating that values is non-empty before computing arithmetic division.",
                "suggested_remediation": "if not values:\n    return 0.0\nreturn float(sum(values)) / len(values)",
                "verification_status": "confirmed"
            },
            {
                "review_id": review_id,
                "title": "Potential SQL Injection in Dynamic Query Formatting",
                "description": "Directly formatting `table_name` into the raw SQL string without identifier quoting allows arbitrary SQL injection.",
                "file_path": "backend/app/demo_sample.py",
                "line_start": 13,
                "line_end": 14,
                "category": "security",
                "severity": "critical",
                "confidence": 0.98,
                "impact": "Full database read/write unauthorized compromise via manipulated table names.",
                "root_cause": "Untrusted input interpolated directly into SQL statement instead of parameterized execution.",
                "suggested_remediation": "Validate table_name against an explicit whitelist of allowed identifiers.",
                "verification_status": "confirmed"
            }
        ]
        created_finding_ids = []
        for sf in sample_findings:
            cf_res = client.post(f"{API_BASE}/findings", json=sf, headers=headers)
            if cf_res.status_code in (200, 201):
                created_finding_ids.append(cf_res.json()["id"])
                print(f"  ✓ Created finding: {sf['title']} ({sf['severity'].upper()})")

        # Generate AutoFix for the first finding
        if created_finding_ids:
            patch_res = client.post(f"{API_BASE}/autofix/generate", json={
                "finding_id": created_finding_ids[0]
            }, headers=headers)
            if patch_res.status_code in (200, 201):
                patch = patch_res.json()
                print(f"  ✓ AutoFix patch generated: {patch['id']} (Status: {patch['status']})")

    print("\n" + "=" * 70)
    print(" SEEDING COMPLETE! You can now log into http://127.0.0.1:5173/")
    print(" Credentials:")
    print("   Email:    architect@openreview.ai")
    print("   Password: OpenReview2026!")
    print("=" * 70)

if __name__ == "__main__":
    seed()
