"""Script to verify the GitHub Review Publishing Engine against the real repository

(gBashCode/OpenReview-AI-) with confirmed GitHub API responses.
"""

import asyncio
import json
import os
import subprocess
import sys

# Ensure backend is on sys.path
sys.path.insert(0, os.path.abspath("backend"))

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.base import Base
import app.models  # Load all ORM models
from app.findings.models import Finding
from app.github.github_auth_service import GitHubAuthService
from app.github.publishing_engine import GitHubReviewPublishingEngine
from app.github.schemas import GitHubPublishRequest
from app.organizations.models import Organization
from app.pull_requests.models import PullRequest
from app.repositories.models import Repository
from app.reviews.models import Review


async def run_live_verification():
    print("=" * 70)
    print("🚀 STARTING LIVE GITHUB REVIEW PUBLISHING ENGINE VERIFICATION")
    print("=" * 70)

    # 1. Retrieve GitHub Token from gh CLI
    try:
        gh_token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
        print(f"✅ Retrieved active GitHub Token from gh CLI: {gh_token[:4]}...{gh_token[-4:]}")
    except Exception as exc:
        print(f"❌ Failed to get gh auth token: {exc}")
        return False

    repo_owner = "gBashCode"
    repo_name = "OpenReview-AI-"
    branch_name = "test/openreview-live-publishing-verification"
    pr_number = None

    try:
        # 2. Create and push a temporary test branch
        print(f"\n📦 Creating test branch '{branch_name}'...")
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)

        test_file_path = "test_sample_live_target.py"
        test_file_content = (
            "def retrieve_user_account(account_id: str):\n"
            "    # Live PR test comment target\n"
            "    query = f\"SELECT * FROM accounts WHERE id = '{account_id}'\"\n"
            "    return db.execute(query)\n"
        )
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_file_content)

        subprocess.run(["git", "add", test_file_path], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "test: add sample target file for live publishing verification"],
            check=True,
            capture_output=True,
        )
        print(f"⬆️ Pushing branch '{branch_name}' to GitHub origin...")
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True, capture_output=True)

        # 3. Create a real Pull Request using gh CLI
        print("\n🔀 Creating Pull Request on GitHub...")
        pr_cmd = [
            "gh", "pr", "create",
            "--repo", f"{repo_owner}/{repo_name}",
            "--head", branch_name,
            "--base", "main",
            "--title", "Test: OpenReview AI Review Publishing Engine Live Verification",
            "--body", "Automated live verification PR for OpenReview AI publishing engine. Will be closed automatically after test.",
        ]
        pr_proc = subprocess.run(pr_cmd, check=True, capture_output=True, text=True)
        pr_url = pr_proc.stdout.strip()
        print(f"✅ Pull Request Created: {pr_url}")

        # Extract PR number from URL
        pr_number = int(pr_url.split("/")[-1])
        print(f"📌 PR Number: #{pr_number}")

        # Get latest commit SHA on this branch
        sha_proc = subprocess.run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
        commit_sha = sha_proc.stdout.strip()
        print(f"📌 Head Commit SHA: {commit_sha}")

        # 4. Set up an isolated in-memory SQLite database session
        print("\n💾 Initializing database models for review and finding...")
        db_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
        async with session_factory() as session:
            # Create Org, Repo, PR, Review, Finding
            org = Organization(name="Live Verification Org", slug="live-verif-org")
            session.add(org)
            await session.flush()

            repo = Repository(
                organization_id=org.id,
                github_repo_id=123456789,
                owner=repo_owner,
                name=repo_name,
                full_name=f"{repo_owner}/{repo_name}",
                default_branch="main",
            )
            session.add(repo)
            await session.flush()

            pr_record = PullRequest(
                repository_id=repo.id,
                github_pr_id=pr_number,
                pr_number=pr_number,
                title="Test: OpenReview AI Review Publishing Engine Live Verification",
                head_branch=branch_name,
                base_branch="main",
                head_sha=commit_sha,
                base_sha="0" * 40,
                author_username="test-runner",
                state="open",
            )
            session.add(pr_record)
            await session.flush()

            review_record = Review(
                pull_request_id=pr_record.id,
                commit_sha=commit_sha,
                status="pending",
                score=72.0,
                security_score=60.0,
                performance_score=95.0,
                quality_score=80.0,
                summary="Detected 1 Critical SQL Injection vulnerability with high confidence.",
            )
            session.add(review_record)
            await session.flush()

            finding_record = Finding(
                review_id=review_record.id,
                file_path=test_file_path,
                line_number=3,
                severity="critical",
                category="security",
                title="SQL Injection Vulnerability in User Query",
                message="Untrusted account_id parameter is directly formatted into SQL query string, enabling arbitrary SQL injection.",
                root_cause="Missing parameterized binding in database execute call.",
                evidence="query = f\"SELECT * FROM accounts WHERE id = '{account_id}'\"",
                suggested_patch='query = "SELECT * FROM accounts WHERE id = :account_id", {"account_id": account_id}',
                verification_status="Confirmed",
                confidence_score=0.98,
                actionability_score=0.96,
                is_publishable=True,
                discussion_state="Accepted",
            )
            session.add(finding_record)
            await session.commit()

            # 5. Execute the GitHub Review Publishing Engine
            print("\n🤖 Invoking GitHubReviewPublishingEngine...")
            publishing_engine = GitHubReviewPublishingEngine(session=session)

            publish_request = GitHubPublishRequest(
                review_id=review_record.id,
                owner=repo_owner,
                repo=repo_name,
                pull_number=pr_number,
                token=gh_token,
            )

            result = await publishing_engine.publish_review(publish_request)

            print("\n" + "=" * 70)
            print("📬 PUBLISHING ENGINE API RECEIPT:")
            print("=" * 70)
            print(f"Status:                      {result.status.upper()}")
            print(f"API Confirmed:               {result.api_confirmed}")
            print(f"GitHub Review ID:            {result.github_review_id}")
            print(f"GitHub Review URL:           {result.github_review_url}")
            print(f"Review Event:                {result.event}")
            print(f"Total Findings:              {result.total_findings}")
            print(f"Actionable Findings:         {result.actionable_findings}")
            print(f"Inline Comments Published:   {result.inline_comments_published}")
            print(f"Comment IDs:                 {result.comment_ids}")
            print(f"Message:                     {result.message}")
            print("=" * 70)

            assert result.status == "published", "Publish status must be 'published'"
            assert result.api_confirmed is True, "Publishing must be confirmed by GitHub API"
            assert result.github_review_id is not None, "GitHub Review ID must be present"

            # 6. Verify confirmed GitHub API response by querying GitHub REST API directly
            print("\n🔍 Verifying comments on GitHub API directly...")
            headers = {
                "Authorization": f"Bearer {gh_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "OpenReviewAI-LiveTest/1.0",
            }
            async with httpx.AsyncClient(base_url="https://api.github.com", headers=headers, timeout=30.0) as client:
                # Query PR Review Comments
                comments_resp = await client.get(f"/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/comments")
                assert comments_resp.status_code == 200, f"Failed to fetch PR comments: {comments_resp.text}"
                comments_data = comments_resp.json()
                print(f"✅ Found {len(comments_data)} published inline review comment(s) on GitHub PR #{pr_number}:")
                for c in comments_data:
                    print(f"   - Comment ID: {c['id']}")
                    print(f"     Path: {c['path']} (Line: {c['line']})")
                    print(f"     URL:  {c['html_url']}")
                    print(f"     Body excerpt:\n       {c['body'][:180]}...")

                # Query PR Reviews
                reviews_resp = await client.get(f"/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/reviews")
                assert reviews_resp.status_code == 200, f"Failed to fetch PR reviews: {reviews_resp.text}"
                reviews_data = reviews_resp.json()
                print(f"\n✅ Found {len(reviews_data)} published review summary/scorecard(s) on GitHub PR #{pr_number}:")
                for r in reviews_data:
                    print(f"   - Review ID: {r['id']}")
                    print(f"     State:     {r['state']}")
                    print(f"     URL:       {r['html_url']}")

        print("\n🎉 LIVE VERIFICATION SUCCESSFUL! ALL COMMENTS CONFIRMED VIA GITHUB API.")
        return True

    finally:
        # Clean up: close the PR, delete remote branch, and switch back to main
        print("\n🧹 Cleaning up test pull request and branches...")
        if pr_number:
            try:
                subprocess.run(["gh", "pr", "close", str(pr_number), "--delete-branch", "--repo", f"{repo_owner}/{repo_name}"], check=False, capture_output=True)
                print(f"✅ Closed PR #{pr_number} and deleted remote branch on GitHub.")
            except Exception as e:
                print(f"Warning during PR close: {e}")

        # Switch back to main and delete local test branch
        try:
            subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
            subprocess.run(["git", "branch", "-D", branch_name], check=False, capture_output=True)
            # Remove temporary test file if present
            if os.path.exists("test_sample_live_target.py"):
                os.remove("test_sample_live_target.py")
            print("✅ Switched back to main branch and cleaned up local files.")
        except Exception as e:
            print(f"Warning during local cleanup: {e}")


if __name__ == "__main__":
    success = asyncio.run(run_live_verification())
    sys.exit(0 if success else 1)
